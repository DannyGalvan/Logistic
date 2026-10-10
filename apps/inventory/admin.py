"""Admin de Django para ``inventory``."""

from __future__ import annotations

from django.contrib import admin

from .models import (
    Alert,
    CycleCount,
    CycleCountLine,
    Lot,
    Stock,
    StockMovement,
)


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    """Admin de lotes."""

    list_display = ("product", "lot_number", "expires_at")
    list_filter = ("product",)
    search_fields = ("lot_number", "product__sku")


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    """Admin de stock."""

    list_display = ("product", "location", "lot", "quantity", "updated_at")
    list_filter = ("location__warehouse",)
    search_fields = ("product__sku", "location__code")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Admin de movimientos (solo lectura)."""

    list_display = (
        "created_at", "movement_type", "product", "quantity", "reference"
    )
    list_filter = ("movement_type", "reason")
    readonly_fields = [f.name for f in StockMovement._meta.fields]

    def has_add_permission(self, request) -> bool:
        """No permite agregar manualmente."""
        return False


@admin.register(CycleCount)
class CycleCountAdmin(admin.ModelAdmin):
    """Admin de conteos."""

    list_display = ("code", "warehouse", "status", "approved_by")
    list_filter = ("status", "warehouse")


@admin.register(CycleCountLine)
class CycleCountLineAdmin(admin.ModelAdmin):
    """Admin de lineas de conteo."""

    list_display = ("cycle_count", "product", "expected_quantity",
                "counted_quantity")


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    """Admin de alertas."""

    list_display = ("alert_type", "product", "is_read", "resolved_at")
    list_filter = ("alert_type", "is_read")
