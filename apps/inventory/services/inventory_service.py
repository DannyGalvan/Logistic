"""Facade ``InventoryService``.

Orquesta los comandos de stock. Cada metodo construye el comando
apropiado y lo ejecuta dentro de ``transaction.atomic``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .commands import (
    AdjustStockCommand,
    IssueStockCommand,
    ReceiveStockCommand,
    TransferStockCommand,
)
from ..events import stock_changed
from .strategies import Allocation, get_strategy


class InventoryService:  # pylint: disable=too-few-public-methods
    """API unificada para todas las operaciones de stock."""

    @staticmethod
    def _run(command):  # type: ignore[no-untyped-def]
        """Ejecuta el comando y notifica ``stock_changed`` (alertas)."""
        movement = command.execute()
        stock_changed.send(sender=InventoryService, product=command.product)
        return movement

    def receive(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        *,
        product: Any,
        location: Any,
        quantity: Decimal,
        unit_cost: Decimal,
        user: Any,
        lot_number: str | None = None,
        expires_at: Any = None,
        manufactured_at: Any = None,
        reference: str = "",
        reason: str = "PURCHASE",
    ):
        """Registra una recepcion de stock."""
        return self._run(ReceiveStockCommand(
            product=product,
            location=location,
            quantity=quantity,
            unit_cost=unit_cost,
            user=user,
            lot_number=lot_number,
            expires_at=expires_at,
            manufactured_at=manufactured_at,
            reference=reference,
            reason=reason,
        ))

    def issue(  # pylint: disable=too-many-arguments
        self,
        *,
        product: Any,
        location: Any,
        quantity: Decimal,
        user: Any,
        lot: Any = None,
        reference: str = "",
        reason: str = "SALE",
    ):
        """Registra una salida de stock."""
        return self._run(IssueStockCommand(
            product=product,
            location=location,
            quantity=quantity,
            user=user,
            lot=lot,
            reference=reference,
            reason=reason,
        ))

    def transfer(  # pylint: disable=too-many-arguments
        self,
        *,
        product: Any,
        from_location: Any,
        to_location: Any,
        quantity: Decimal,
        user: Any,
        lot: Any = None,
        reference: str = "",
    ):
        """Registra una transferencia entre dos ubicaciones."""
        return self._run(TransferStockCommand(
            product=product,
            from_location=from_location,
            to_location=to_location,
            quantity=quantity,
            user=user,
            lot=lot,
            reference=reference,
        ))

    def adjust(  # pylint: disable=too-many-arguments
        self,
        *,
        product: Any,
        location: Any,
        counted_quantity: Decimal,
        user: Any,
        lot: Any = None,
        reason: str = "CORRECTION",
        note: str = "",
    ):
        """Ajusta la cantidad en una ubicacion al valor contado."""
        return self._run(AdjustStockCommand(
            product=product,
            location=location,
            counted_quantity=counted_quantity,
            user=user,
            lot=lot,
            reason=reason,
            note=note,
        ))

    def allocate(
        self,
        *,
        product: Any,
        warehouse: Any,
        quantity: Decimal,
    ) -> list[Allocation]:
        """Asigna ``quantity`` siguiendo la estrategia del producto."""
        strategy = get_strategy(product.rotation_strategy)
        return strategy.allocate(product, warehouse, quantity)


__all__ = ["InventoryService"]
