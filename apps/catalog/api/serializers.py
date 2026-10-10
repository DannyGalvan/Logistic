"""Serializers de ``catalog``."""

from __future__ import annotations

from rest_framework import serializers

from ..models import Brand, Category, Product, UnitOfMeasure


class CategorySerializer(serializers.ModelSerializer):
    """Categoria de productos."""

    class Meta:
        model = Category
        fields = ["id", "name", "parent", "description", "is_active"]
        read_only_fields = ["is_active"]


class BrandSerializer(serializers.ModelSerializer):
    """Marca."""

    class Meta:
        model = Brand
        fields = ["id", "name", "is_active"]
        read_only_fields = ["is_active"]


class UnitOfMeasureSerializer(serializers.ModelSerializer):
    """Unidad de medida."""

    class Meta:
        model = UnitOfMeasure
        fields = ["id", "code", "name", "is_active"]
        read_only_fields = ["is_active"]


class ProductSerializer(serializers.ModelSerializer):
    """Producto; ``cost_price`` lo calcula el inventario (solo lectura)."""

    class Meta:
        model = Product
        fields = [
            "id", "sku", "barcode", "name", "description", "category", "brand",
            "uom", "cost_price", "sale_price", "min_stock", "max_stock",
            "reorder_point", "track_lots", "track_expiry", "rotation_strategy",
            "is_active",
        ]
        read_only_fields = ["cost_price", "is_active"]
