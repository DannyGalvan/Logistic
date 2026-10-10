"""Estrategias de asignacion de stock (FIFO / FEFO).

Patron Strategy + Registry. ``STRATEGIES`` mapea ``Product.rotation_strategy``
a la clase correspondiente.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

from django.db.models import F, Q

from apps.core.exceptions import InsufficientStockError
from apps.inventory.models import Stock
from apps.warehouses.models import Location


@dataclass(frozen=True)
class Allocation:
    """Resultado de una asignacion de stock."""

    stock_id: int
    location_id: int
    lot_id: int | None
    quantity: Decimal


class AllocationStrategy(Protocol):
    """Contrato para las estrategias de asignacion."""

    def allocate(self, product: Any, warehouse: Any, quantity: Decimal) -> list[Allocation]:
        """Devuelve una lista de ``Allocation`` que suman ``quantity``."""


class FIFOStrategy:
    """Asignacion primero en entrar, primero en salir."""

    def allocate(
        self, product: Any, warehouse: Any, quantity: Decimal,
    ) -> list[Allocation]:
        """Devuelve allocations ordenados por antiguedad del lote."""
        candidates = (
            Stock.objects.filter(product=product, quantity__gt=0)
            .filter(location__warehouse=warehouse)
            .filter(location__location_type__in=[
                Location.LocationType.RECEIVING,
                Location.LocationType.STORAGE,
                Location.LocationType.PICKING,
            ])
            .order_by("lot__created_at", "id")
        )
        return _consume(candidates, quantity)


class FEFOStrategy:
    """Asignacion primero en expirar, primero en salir."""

    def allocate(
        self, product: Any, warehouse: Any, quantity: Decimal,
    ) -> list[Allocation]:
        """Devuelve allocations ordenados por ``lot.expires_at``."""
        candidates = (
            Stock.objects.filter(product=product, quantity__gt=0)
            .filter(location__warehouse=warehouse)
            .filter(location__location_type__in=[
                Location.LocationType.RECEIVING,
                Location.LocationType.STORAGE,
                Location.LocationType.PICKING,
            ])
            .filter(Q(lot__isnull=True) | Q(lot__expires_at__isnull=False))
            .order_by(F("lot__expires_at").asc(nulls_last=True), "id")
        )
        return _consume(candidates, quantity)


def _consume(candidates, quantity: Decimal) -> list[Allocation]:
    """Consume ``quantity`` de la ``lista`` de stocks candidatos."""
    allocations: list[Allocation] = []
    remaining = Decimal(quantity)
    for stock in candidates:
        if remaining <= 0:
            break
        take = min(stock.quantity, remaining)
        if take <= 0:
            continue
        allocations.append(
            Allocation(
                stock_id=stock.pk,
                location_id=stock.location_id,
                lot_id=stock.lot_id,
                quantity=take,
            )
        )
        remaining -= take
    if remaining > 0:
        raise InsufficientStockError(
            f"Stock insuficiente: faltan {remaining} unidades."
        )
    return allocations


STRATEGIES: dict[str, type[FIFOStrategy] | type[FEFOStrategy]] = {
    "FIFO": FIFOStrategy,
    "FEFO": FEFOStrategy,
}


def get_strategy(name: str) -> FIFOStrategy | FEFOStrategy:
    """Devuelve la estrategia por nombre (``FIFO`` por defecto)."""
    return STRATEGIES.get(name, FIFOStrategy)()


__all__ = [
    "Allocation",
    "AllocationStrategy",
    "FIFOStrategy",
    "FEFOStrategy",
    "STRATEGIES",
    "get_strategy",
]
