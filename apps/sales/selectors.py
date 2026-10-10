"""Selectors de ``sales``."""

from __future__ import annotations

from django.db.models import QuerySet

from .models import SalesOrder, Shipment


def orders(filters: dict | None = None) -> QuerySet[SalesOrder]:
    """Lista de ordenes filtrada."""
    qs = SalesOrder.objects.select_related("customer", "warehouse")
    if filters:
        qs = qs.filter(**filters)
    return qs


def shipments(filters: dict | None = None) -> QuerySet[Shipment]:
    """Lista de despachos filtrada."""
    qs = Shipment.objects.select_related("order")
    if filters:
        qs = qs.filter(**filters)
    return qs


__all__ = ["orders", "shipments"]
