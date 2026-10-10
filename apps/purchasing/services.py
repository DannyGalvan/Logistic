"""Servicios de ``purchasing``.

``PurchaseService`` orquesta el ciclo de la orden: alta, confirmacion,
recepcion (parcial o total) y cancelacion. Las operaciones de stock
delegan en ``InventoryService``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.core.models import next_code
from apps.core.state import StateMachine
from apps.inventory.services import InventoryService

from .models import (
    GoodsReceipt,
    GoodsReceiptLine,
    PurchaseOrder,
    PurchaseOrderLine,
)


ORDER_TRANSITIONS: dict[str, list[str]] = {
    "DRAFT": ["CONFIRMED", "CANCELLED"],
    "CONFIRMED": ["PARTIALLY_RECEIVED", "RECEIVED", "CANCELLED"],
    "PARTIALLY_RECEIVED": ["PARTIALLY_RECEIVED", "RECEIVED"],
}


@dataclass
class ReceiptLineInput:
    """DTO para una linea de recepcion."""

    order_line_id: int
    quantity: Decimal
    lot_number: str = ""
    expires_at: Any = None


class PurchaseService:
    """API de gestion de ordenes de compra."""

    def __init__(self, inventory: Any = None) -> None:
        """Guarda la dependencia del ``InventoryService``."""
        self.inventory = inventory or InventoryService()
        self.machine = StateMachine(ORDER_TRANSITIONS)

    @transaction.atomic
    def create_order(
        self,
        *,
        supplier: Any,
        warehouse: Any,
        order_date: Any,
        expected_date: Any | None = None,
        notes: str = "",
        user: Any = None,
    ) -> PurchaseOrder:
        """Crea una orden en ``DRAFT``."""
        return PurchaseOrder.objects.create(
            code=next_code("OC"),
            supplier=supplier,
            warehouse=warehouse,
            order_date=order_date,
            expected_date=expected_date,
            notes=notes,
            created_by=user,
            updated_by=user,
        )

    @transaction.atomic
    def add_line(
        self,
        order: PurchaseOrder,
        *,
        product: Any,
        quantity: Decimal,
        unit_cost: Decimal,
    ) -> PurchaseOrderLine:
        """Agrega una linea a la orden (solo DRAFT)."""
        if not order.is_editable:
            raise ValidationError("Solo se editan ordenes en borrador.")
        return PurchaseOrderLine.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            unit_cost=unit_cost,
        )

    @transaction.atomic
    def confirm(self, order: PurchaseOrder) -> PurchaseOrder:
        """Confirma la orden (DRAFT -> CONFIRMED)."""
        self.machine.assert_can_transition(order.status, "CONFIRMED")
        if not order.lines.exists():
            raise ValidationError("La orden no tiene lineas.")
        order.status = "CONFIRMED"
        order.save(update_fields=["status", "updated_at"])
        return order

    @transaction.atomic
    def cancel(self, order: PurchaseOrder) -> PurchaseOrder:
        """Cancela la orden."""
        self.machine.assert_can_transition(order.status, "CANCELLED")
        order.status = "CANCELLED"
        order.save(update_fields=["status", "updated_at"])
        return order

    @transaction.atomic
    def receive(
        self,
        order: PurchaseOrder,
        *,
        location: Any,
        lines: list[ReceiptLineInput],
        user: Any,
    ) -> GoodsReceipt:
        """Registra la recepcion parcial o total de mercancia."""
        if order.status not in ("CONFIRMED", "PARTIALLY_RECEIVED"):
            raise ValidationError("La orden no admite recepcion.")
        receipt = GoodsReceipt.objects.create(
            code=next_code("REC"),
            order=order,
            location=location,
            created_by=user,
            updated_by=user,
        )
        any_partial = False
        any_received = True
        for line_input in lines:
            order_line = PurchaseOrderLine.objects.select_for_update().get(
                pk=line_input.order_line_id
            )
            pending = order_line.pending_quantity
            if line_input.quantity > pending:
                raise ValidationError(
                    f"Cantidad a recibir excede lo pendiente ({pending})."
                )
            movement = self.inventory.receive(
                product=order_line.product,
                location=location,
                quantity=line_input.quantity,
                unit_cost=order_line.unit_cost,
                user=user,
                lot_number=line_input.lot_number or None,
                expires_at=line_input.expires_at,
                reference=order.code,
                reason="PURCHASE",
            )
            order_line.received_quantity += line_input.quantity
            order_line.save(update_fields=["received_quantity"])
            GoodsReceiptLine.objects.create(
                receipt=receipt,
                order_line=order_line,
                quantity=line_input.quantity,
                lot_number=line_input.lot_number,
                expires_at=line_input.expires_at,
                movement=movement,
            )
            if order_line.pending_quantity > 0:
                any_partial = True
                any_received = False
        order.status = "RECEIVED" if any_received else "PARTIALLY_RECEIVED"
        if any_partial:
            order.status = "PARTIALLY_RECEIVED"
        else:
            order.status = "RECEIVED"
        order.save(update_fields=["status", "updated_at"])
        return receipt


__all__ = [
    "PurchaseService",
    "ORDER_TRANSITIONS",
    "ReceiptLineInput",
]
