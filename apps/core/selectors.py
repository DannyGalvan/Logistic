"""Consultas de lectura transversales del nucleo (dashboard, contadores).

Usa ``apps.get_model`` para no acoplar ``core`` a las apps de dominio
en tiempo de importacion.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.apps import apps
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce


def low_stock_products(limit: int | None = None):
    """Productos activos con existencia total por debajo de ``min_stock``."""
    product_model = apps.get_model("catalog", "Product")
    qs = (
        product_model.active.filter(min_stock__gt=0)
        .annotate(
            on_hand=Coalesce(
                Sum("stocks__quantity"),
                Value(Decimal("0")),
                output_field=DecimalField(max_digits=14, decimal_places=3),
            )
        )
        .filter(on_hand__lt=F("min_stock"))
        .order_by("on_hand")
    )
    return qs[:limit] if limit else qs


def unread_alerts_count() -> int:
    """Numero de alertas sin leer."""
    return apps.get_model("inventory", "Alert").objects.filter(is_read=False).count()


def dashboard_context() -> dict[str, Any]:
    """KPIs, ultimos movimientos y productos bajo minimo."""
    product_model = apps.get_model("catalog", "Product")
    warehouse_model = apps.get_model("warehouses", "Warehouse")
    movement_model = apps.get_model("inventory", "StockMovement")
    purchase_model = apps.get_model("purchasing", "PurchaseOrder")
    sales_model = apps.get_model("sales", "SalesOrder")

    pending_purchases = purchase_model.objects.exclude(
        Q(status=purchase_model.Status.RECEIVED)
        | Q(status=purchase_model.Status.CANCELLED)
    ).count()
    pending_sales = sales_model.objects.exclude(
        Q(status=sales_model.Status.SHIPPED)
        | Q(status=sales_model.Status.CANCELLED)
    ).count()
    return {
        "kpis": {
            "products": product_model.active.count(),
            "warehouses": warehouse_model.active.count(),
            "low_stock": low_stock_products().count(),
            "pending_orders": pending_purchases + pending_sales,
            "pending_purchases": pending_purchases,
            "pending_sales": pending_sales,
        },
        "recent_movements": movement_model.objects.select_related(
            "product", "from_location", "to_location"
        ).order_by("-created_at")[:8],
        "low_stock": low_stock_products(limit=6),
    }


__all__ = ["dashboard_context", "low_stock_products", "unread_alerts_count"]
