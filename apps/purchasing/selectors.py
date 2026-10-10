"""Selectors de ``purchasing``."""

from __future__ import annotations

from django.db.models import QuerySet

from .models import GoodsReceipt, PurchaseOrder


def orders(filters: dict | None = None) -> QuerySet[PurchaseOrder]:
    """Lista de ordenes filtrada."""
    qs = PurchaseOrder.objects.select_related("supplier", "warehouse")
    if filters:
        qs = qs.filter(**filters)
    return qs


def receipts(filters: dict | None = None) -> QuerySet[GoodsReceipt]:
    """Lista de recepciones filtrada."""
    qs = GoodsReceipt.objects.select_related("order", "location")
    if filters:
        qs = qs.filter(**filters)
    return qs


__all__ = ["orders", "receipts"]
