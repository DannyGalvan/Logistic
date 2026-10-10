"""Servicio de conteos ciclicos (CycleCount).

Plan section 6.6. ``CycleCountService`` maneja el ciclo de vida:
``create``, ``start``, ``record`` y ``approve``. Las transiciones
pasan por ``StateMachine``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.core.models import next_code
from apps.core.state import StateMachine
from apps.inventory.models import CycleCount, CycleCountLine, Stock

from .inventory_service import InventoryService


CYCLE_COUNT_TRANSITIONS: dict[str, list[str]] = {
    "DRAFT": ["IN_PROGRESS", "CANCELLED"],
    "IN_PROGRESS": ["APPROVED", "CANCELLED"],
}


class CycleCountService:
    """API de gestion de conteos ciclicos."""

    def __init__(self, inventory: Any = None) -> None:
        """Guarda la dependencia opcional al ``InventoryService``."""
        self.inventory = inventory or InventoryService()
        self.machine = StateMachine(CYCLE_COUNT_TRANSITIONS)

    @transaction.atomic
    def create(
        self,
        *,
        warehouse: Any,
        user: Any,
        location: Any | None = None,
    ) -> CycleCount:
        """Crea un conteo en ``DRAFT`` con snapshot del stock actual."""
        cycle = CycleCount.objects.create(
            code=next_code("CC"),
            warehouse=warehouse,
            location=location,
            status="DRAFT",
            created_by=user,
            updated_by=user,
        )
        qs = Stock.objects.filter(
            location__warehouse=warehouse,
            quantity__gt=0,
        )
        if location is not None:
            qs = qs.filter(location=location)
        for stock in qs.select_related("product", "location", "lot"):
            CycleCountLine.objects.create(
                cycle_count=cycle,
                product=stock.product,
                location=stock.location,
                lot=stock.lot,
                expected_quantity=stock.quantity,
            )
        return cycle

    @transaction.atomic
    def start(self, cycle: CycleCount) -> CycleCount:
        """Pasa de ``DRAFT`` a ``IN_PROGRESS``."""
        self.machine.assert_can_transition(cycle.status, "IN_PROGRESS")
        cycle.status = "IN_PROGRESS"
        cycle.save(update_fields=["status", "updated_at"])
        return cycle

    @transaction.atomic
    def record(
        self,
        line: CycleCountLine,
        counted_quantity: Decimal,
    ) -> CycleCountLine:
        """Registra la cantidad contada en una linea."""
        if line.cycle_count.status != "IN_PROGRESS":
            raise ValidationError("El conteo debe estar en progreso.")
        line.counted_quantity = counted_quantity
        line.save(update_fields=["counted_quantity"])
        return line

    @transaction.atomic
    def approve(
        self,
        cycle: CycleCount,
        user: Any,
    ) -> CycleCount:
        """Aprueba el conteo y aplica los ajustes correspondientes."""
        self.machine.assert_can_transition(cycle.status, "APPROVED")
        lines = list(cycle.lines.select_related("product", "location", "lot"))
        if any(line.counted_quantity is None for line in lines):
            raise ValidationError("Todas las lineas deben estar contadas.")
        for line in lines:
            if line.counted_quantity == line.expected_quantity:
                continue
            self.inventory.adjust(
                product=line.product,
                location=line.location,
                counted_quantity=line.counted_quantity,
                user=user,
                lot=line.lot,
                reason="COUNT",
                note=f"Conteo CC-{cycle.code}",
            )
        cycle.status = "APPROVED"
        cycle.approved_by = user
        cycle.approved_at = timezone.now()
        cycle.save(
            update_fields=["status", "approved_by", "approved_at", "updated_at"]
        )
        return cycle

    @transaction.atomic
    def cancel(self, cycle: CycleCount) -> CycleCount:
        """Cancela un conteo en ``DRAFT`` o ``IN_PROGRESS``."""
        self.machine.assert_can_transition(cycle.status, "CANCELLED")
        cycle.status = "CANCELLED"
        cycle.save(update_fields=["status", "updated_at"])
        return cycle


__all__ = [
    "CycleCountService",
    "CYCLE_COUNT_TRANSITIONS",
]
