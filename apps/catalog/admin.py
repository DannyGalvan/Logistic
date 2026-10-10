"""Admin de Django para ``catalog``."""

from __future__ import annotations

from django.contrib import admin

from .models import Brand, Category, Product, UnitOfMeasure


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin de categorias."""

    list_display = ("name", "parent", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Admin de marcas."""

    list_display = ("name", "is_active")
    search_fields = ("name",)


@admin.register(UnitOfMeasure)
class UnitAdmin(admin.ModelAdmin):
    """Admin de unidades de medida."""

    list_display = ("code", "name", "is_active")
    search_fields = ("code", "name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin de productos."""

    list_display = ("sku", "name", "category", "uom", "is_active")
    list_filter = ("category", "uom", "is_active", "track_lots", "track_expiry")
    search_fields = ("sku", "name", "barcode")
