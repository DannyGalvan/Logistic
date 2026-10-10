"""Comandos de movimiento de stock (patron Command).

Cada comando valida la operacion y, al ejecutarse dentro de una
transaccion, persiste los cambios sobre ``Stock`` y registra un
``StockMovement``. Los comandos se invocan desde
``InventoryService``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

from django.db import transaction

from apps.core.exceptions import (
    BusinessRuleError,
    InsufficientStockError,
    InvalidQuantityError,
    LotRequiredError,
)
from apps.inventory.models import Lot, Stock, StockMovement


class StockCommand(Protocol):
    """Contrato de un comando de stock."""

    def execute(self) -> StockMovement | None:
        """Ejecuta el comando y devuelve el movimiento persistido."""


@dataclass
class ReceiveStockCommand:
    """Comando para recibir stock en una ubicacion."""

    product: Any
    location: Any
    quantity: Decimal
    unit_cost: Decimal
    user: Any
    lot_number: str | None = None
    expires_at: Any = None
    manufactured_at: Any = None
    reference: str = ""
    reason: str = "PURCHASE"

    def __post_init__(self) -> None:
        """Valida el payload al construir el comando."""
        if self.quantity <= 0:
            raise InvalidQuantityError("La cantidad debe ser mayor a cero.")

    def execute(self) -> StockMovement:
        """Persiste la recepcion y devuelve el movimiento."""
        with transaction.atomic():
            lot: Lot | None = None
            if self.product.track_lots and self.lot_number:
                lot, _ = Lot.objects.get_or_create(
                    product=self.product,
                    lot_number=self.lot_number,
                    defaults={
                        "expires_at": self.expires_at,
                        "manufactured_at": self.manufactured_at,
                    },
                )
            elif self.product.track_lots and not self.lot_number:
                raise LotRequiredError(
                    f"El producto {self.product.sku} requiere numero de lote."
                )
            stock, _ = Stock.objects.select_for_update().get_or_create(
                product=self.product,
                location=self.location,
                lot=lot,
                defaults={"quantity": Decimal("0")},
            )
            total_qty = stock.quantity + self.quantity
            wac = (
                (stock.quantity * Decimal(str(self.product.cost_price))
                 + self.quantity * self.unit_cost)
                / total_qty
            )
            self.product.cost_price = wac.quantize(Decimal("0.0001"))
            self.product.save(update_fields=["cost_price"])
            stock.quantity = total_qty
            stock.save(update_fields=["quantity", "updated_at"])
            return StockMovement.objects.create(
                movement_type="RECEIPT",
                product=self.product,
                lot=lot,
                to_location=self.location,
                quantity=self.quantity,
                unit_cost=self.unit_cost,
                reason=self.reason,
                reference=self.reference,
                created_by=self.user,
            )


@dataclass
class IssueStockCommand:
    """Comando para sacar stock de una ubicacion."""

    product: Any
    location: Any
    quantity: Decimal
    user: Any
    lot: Any = None
    reference: str = ""
    reason: str = "SALE"

    def __post_init__(self) -> None:
        """Valida el payload al construir el comando."""
        if self.quantity <= 0:
            raise InvalidQuantityError("La cantidad debe ser mayor a cero.")

    def execute(self) -> StockMovement:
        """Persiste la salida y devuelve el movimiento."""
        with transaction.atomic():
            stock = (
                Stock.objects.select_for_update()
                .filter(
                    product=self.product,
                    location=self.location,
                    lot=self.lot,
                )
                .first()
            )
            if stock is None or stock.quantity < self.quantity:
                available = stock.quantity if stock else Decimal("0")
                raise InsufficientStockError(
                    f"Stock disponible {available}, requerido {self.quantity}."
                )
            stock.quantity -= self.quantity
            stock.save(update_fields=["quantity", "updated_at"])
            return StockMovement.objects.create(
                movement_type="ISSUE",
                product=self.product,
                lot=self.lot,
                from_location=self.location,
                quantity=self.quantity,
                unit_cost=self.product.cost_price,
                reason=self.reason,
                reference=self.reference,
                created_by=self.user,
            )


@dataclass
class TransferStockCommand:
    """Comando para transferir stock entre dos ubicaciones."""

    product: Any
    from_location: Any
    to_location: Any
    quantity: Decimal
    user: Any
    lot: Any = None
    reference: str = ""

    def __post_init__(self) -> None:
        """Valida ubicaciones distintas y cantidad positiva."""
        if self.quantity <= 0:
            raise InvalidQuantityError("La cantidad debe ser mayor a cero.")
        if self.from_location.pk == self.to_location.pk:
            raise BusinessRuleError(
                "Origen y destino deben ser ubicaciones distintas."
            )

    def execute(self) -> StockMovement:
        """Aplica la transferencia atomica y devuelve el movimiento."""
        with transaction.atomic():
            origin = (
                Stock.objects.select_for_update()
                .filter(
                    product=self.product,
                    location=self.from_location,
                    lot=self.lot,
                )
                .first()
            )
            if origin is None or origin.quantity < self.quantity:
                available = origin.quantity if origin else Decimal("0")
                raise InsufficientStockError(
                    f"Stock disponible {available}, requerido {self.quantity}."
                )
            origin.quantity -= self.quantity
            origin.save(update_fields=["quantity", "updated_at"])
            dest, _ = Stock.objects.select_for_update().get_or_create(
                product=self.product,
                location=self.to_location,
                lot=self.lot,
                defaults={"quantity": Decimal("0")},
            )
            dest.quantity += self.quantity
            dest.save(update_fields=["quantity", "updated_at"])
            return StockMovement.objects.create(
                movement_type="TRANSFER",
                product=self.product,
                lot=self.lot,
                from_location=self.from_location,
                to_location=self.to_location,
                quantity=self.quantity,
                unit_cost=self.product.cost_price,
                reason="INTERNAL",
                reference=self.reference,
                created_by=self.user,
            )


@dataclass
class AdjustStockCommand:
    """Comando para ajustar la cantidad de una ubicacion al valor contado."""

    product: Any
    location: Any
    counted_quantity: Decimal
    user: Any
    lot: Any = None
    reason: str = "CORRECTION"
    note: str = ""

    def execute(self) -> StockMovement | None:
        """Aplica el ajuste y devuelve el movimiento (o ``None`` si delta=0)."""
        with transaction.atomic():
            stock, _ = Stock.objects.select_for_update().get_or_create(
                product=self.product,
                location=self.location,
                lot=self.lot,
                defaults={"quantity": Decimal("0")},
            )
            delta = self.counted_quantity - stock.quantity
            if delta == 0:
                return None
            stock.quantity = self.counted_quantity
            stock.save(update_fields=["quantity", "updated_at"])
            movement_type = "ADJUSTMENT_IN" if delta > 0 else "ADJUSTMENT_OUT"
            kwargs: dict[str, Any] = {
                "movement_type": movement_type,
                "product": self.product,
                "lot": self.lot,
                "quantity": abs(delta),
                "unit_cost": self.product.cost_price,
                "reason": self.reason,
                "note": self.note,
                "created_by": self.user,
            }
            if movement_type == "ADJUSTMENT_IN":
                kwargs["to_location"] = self.location
            else:
                kwargs["from_location"] = self.location
            return StockMovement.objects.create(**kwargs)


__all__ = [
    "StockCommand",
    "ReceiveStockCommand",
    "IssueStockCommand",
    "TransferStockCommand",
    "AdjustStockCommand",
]
