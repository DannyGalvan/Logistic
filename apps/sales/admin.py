"""Admin de Django para ``sales``."""

from __future__ import annotations

from django.contrib import admin

from .models import (
    SalesOrder,
    SalesOrderLine,
    Shipment,
    ShipmentLine,
)


class SalesOrderLineInline(admin.TabularInline):
    """Inline de lineas para la orden."""

    model = SalesOrderLine
    extra = 0


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    """Admin de ordenes de venta."""

    list_display = ("code", "customer", "warehouse", "status", "order_date")
    list_filter = ("status", "customer")
    search_fields = ("code", "customer__name")
    inlines = [SalesOrderLineInline]


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    """Admin de despachos."""

    list_display = ("code", "order", "carrier", "shipped_at")


@admin.register(ShipmentLine)
class ShipmentLineAdmin(admin.ModelAdmin):
    """Admin de lineas de despacho."""

    list_display = ("shipment", "order_line", "location", "quantity")
