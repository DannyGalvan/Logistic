"""Admin de Django para ``warehouses``."""

from __future__ import annotations

from django.contrib import admin

from .models import Location, Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    """Admin de almacenes."""

    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name", "address")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Admin de ubicaciones."""

    list_display = ("warehouse", "code", "name", "location_type", "is_active")
    list_filter = ("warehouse", "location_type", "is_active")
    search_fields = ("code", "name")
