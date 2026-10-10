"""Admin de Django para ``purchasing``."""

from __future__ import annotations

from django.contrib import admin

from .models import (
    GoodsReceipt,
    GoodsReceiptLine,
    PurchaseOrder,
    PurchaseOrderLine,
)


class PurchaseOrderLineInline(admin.TabularInline):
    """Inline de lineas para la orden."""

    model = PurchaseOrderLine
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    """Admin de ordenes de compra."""

    list_display = ("code", "supplier", "warehouse", "status", "order_date")
    list_filter = ("status", "supplier")
    search_fields = ("code", "supplier__name")
    inlines = [PurchaseOrderLineInline]


@admin.register(GoodsReceipt)
class GoodsReceiptAdmin(admin.ModelAdmin):
    """Admin de recepciones."""

    list_display = ("code", "order", "location", "received_at")
    list_filter = ("location",)


@admin.register(GoodsReceiptLine)
class GoodsReceiptLineAdmin(admin.ModelAdmin):
    """Admin de lineas de recepcion."""

    list_display = ("receipt", "order_line", "quantity")
