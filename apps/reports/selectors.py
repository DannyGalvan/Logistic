"""Selectors para construir KPIs y datasets de reportes."""

from __future__ import annotations

import datetime
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.catalog.models import Product
from apps.inventory.models import Lot, Stock, StockMovement
from apps.purchasing.models import PurchaseOrder
from apps.sales.models import SalesOrder
from apps.warehouses.models import Warehouse


def dashboard_kpis() -> dict[str, object]:
    """KPIs agregados para el dashboard."""
    products = Product.objects.filter(is_active=True)
    stock_value = sum(
        (s.quantity * s.product.cost_price for s in Stock.objects.all()),
        Decimal("0"),
    )
    return {
        "products": products.count(),
        "warehouses": Warehouse.active.count(),
        "low_stock": products.filter(reorder_point__gt=0).count(),
        "pending_orders": (
            PurchaseOrder.objects.exclude(
                status__in=["RECEIVED", "CANCELLED"]
            ).count()
            + SalesOrder.objects.exclude(
                status__in=["SHIPPED", "CANCELLED"]
            ).count()
        ),
        "expiring_lots": Lot.objects.filter(
            expires_at__lte=timezone.now().date()
            + datetime.timedelta(days=30),
        ).count(),
        "movements_today": StockMovement.objects.filter(
            created_at__date=timezone.now().date(),
        ).count(),
        "stock_value": stock_value,
    }


def inventory_valuation(warehouse=None) -> Decimal:
    """Valor total del inventario."""
    qs = Stock.objects.all()
    if warehouse is not None:
        qs = qs.filter(location__warehouse=warehouse)
    return sum(
        (s.quantity * s.product.cost_price for s in qs),
        Decimal("0"),
    )


def top_moving_products(days: int = 30, limit: int = 10):
    """Productos con mas salidas en ``days`` dias."""
    since = timezone.now() - datetime.timedelta(days=days)
    return (
        StockMovement.objects.filter(
            created_at__gte=since,
            movement_type__in=["ISSUE", "ADJUSTMENT_OUT"],
        )
        .values("product__sku", "product__name")
        .annotate(total=Sum("quantity"))
        .order_by("-total")[:limit]
    )


def movements_by_day(days: int = 30):
    """Movimientos agrupados por dia."""
    since = timezone.now().date() - datetime.timedelta(days=days)
    return (
        StockMovement.objects.filter(created_at__date__gte=since)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )


__all__ = [
    "dashboard_kpis",
    "inventory_valuation",
    "top_moving_products",
    "movements_by_day",
]
