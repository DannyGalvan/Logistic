"""Servicios de ``sales``.

``SalesService`` orquesta el ciclo de la orden de venta: alta,
confirmacion, cancelacion y despacho. Las operaciones de stock
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
from apps.inventory.models import Lot
from apps.inventory.services import InventoryService
from apps.warehouses.models import Location

from .models import (
    SalesOrder,
    SalesOrderLine,
    Shipment,
    ShipmentLine,
)


ORDER_TRANSITIONS: dict[str, list[str]] = {
    "DRAFT": ["CONFIRMED", "CANCELLED"],
    "CONFIRMED": ["PARTIALLY_SHIPPED", "SHIPPED", "CANCELLED"],
    "PARTIALLY_SHIPPED": ["PARTIALLY_SHIPPED", "SHIPPED"],
}


@dataclass
class ShipLineInput:
    """DTO para una linea de despacho."""

    order_line_id: int
    location_id: int
    lot_id: int | None
    quantity: Decimal


class SalesService:
    """API de gestion de ordenes de venta."""

    def __init__(self, inventory: Any = None) -> None:
        """Guarda la dependencia del ``InventoryService``."""
        self.inventory = inventory or InventoryService()
        self.machine = StateMachine(ORDER_TRANSITIONS)

    @transaction.atomic
    def create_order(
        self,
        *,
        customer: Any,
        warehouse: Any,
        order_date: Any,
        notes: str = "",
        user: Any = None,
    ) -> SalesOrder:
        """Crea una orden en ``DRAFT``."""
        return SalesOrder.objects.create(
            code=next_code("OV"),
            customer=customer,
            warehouse=warehouse,
            order_date=order_date,
            notes=notes,
            created_by=user,
            updated_by=user,
        )

    @transaction.atomic
    def add_line(
        self,
        order: SalesOrder,
        *,
        product: Any,
        quantity: Decimal,
        unit_price: Decimal,
    ) -> SalesOrderLine:
        """Agrega una linea."""
        if not order.is_editable:
            raise ValidationError("Solo se editan ordenes en borrador.")
        return SalesOrderLine.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            unit_price=unit_price,
        )

    @transaction.atomic
    def confirm(self, order: SalesOrder) -> SalesOrder:
        """Confirma la orden."""
        self.machine.assert_can_transition(order.status, "CONFIRMED")
        if not order.lines.exists():
            raise ValidationError("La orden no tiene lineas.")
        order.status = "CONFIRMED"
        order.save(update_fields=["status", "updated_at"])
        return order

    @transaction.atomic
    def cancel(self, order: SalesOrder) -> SalesOrder:
        """Cancela la orden."""
        self.machine.assert_can_transition(order.status, "CANCELLED")
        order.status = "CANCELLED"
        order.save(update_fields=["status", "updated_at"])
        return order

    @transaction.atomic
    def suggest_picking(self, order: SalesOrder) -> list[dict[str, Any]]:
        """Sugiere ubicaciones/lotes para picking."""
        suggestions: list[dict[str, Any]] = []
        for line in order.lines.all():
            allocations = self.inventory.allocate(
                product=line.product,
                warehouse=order.warehouse,
                quantity=line.pending_quantity,
            )
            for alloc in allocations:
                suggestions.append({
                    "order_line_id": line.pk,
                    "location_id": alloc.location_id,
                    "lot_id": alloc.lot_id,
                    "quantity": alloc.quantity,
                })
        return suggestions

    @transaction.atomic
    def ship(
        self,
        order: SalesOrder,
        *,
        lines: list[ShipLineInput],
        user: Any,
        carrier: str = "",
        tracking_number: str = "",
    ) -> Shipment:
        """Registra el despacho parcial o total."""
        if order.status not in ("CONFIRMED", "PARTIALLY_SHIPPED"):
            raise ValidationError("La orden no admite despacho.")
        shipment = Shipment.objects.create(
            code=next_code("DES"),
            order=order,
            carrier=carrier,
            tracking_number=tracking_number,
            created_by=user,
            updated_by=user,
        )
        any_partial = False
        for line_input in lines:
            order_line = SalesOrderLine.objects.select_for_update().get(
                pk=line_input.order_line_id
            )
            pending = order_line.pending_quantity
            if line_input.quantity > pending:
                raise ValidationError(
                    f"Cantidad excede lo pendiente ({pending})."
                )
            location = Location.objects.get(pk=line_input.location_id)
            lot = (
                Lot.objects.get(pk=line_input.lot_id)
                if line_input.lot_id else None
            )
            movement = self.inventory.issue(
                product=order_line.product,
                location=location,
                quantity=line_input.quantity,
                user=user,
                lot=lot,
                reference=order.code,
                reason="SALE",
            )
            order_line.shipped_quantity += line_input.quantity
            order_line.save(update_fields=["shipped_quantity"])
            ShipmentLine.objects.create(
                shipment=shipment,
                order_line=order_line,
                location=location,
                lot=lot,
                quantity=line_input.quantity,
                movement=movement,
            )
            if order_line.pending_quantity > 0:
                any_partial = True
        order.status = (
            "PARTIALLY_SHIPPED" if any_partial else "SHIPPED"
        )
        order.save(update_fields=["status", "updated_at"])
        return shipment


__all__ = [
    "SalesService",
    "ORDER_TRANSITIONS",
    "ShipLineInput",
]
