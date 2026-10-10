"""Formularios de la app ``catalog``.

Cuatro ``ModelForm`` para las entidades del catalogo. ``ProductForm``
incluye validacion cruzada ``track_expiry`` -> ``track_lots``.
"""

from __future__ import annotations

from django import forms

from .models import Brand, Category, Product, UnitOfMeasure


class CategoryForm(forms.ModelForm):
    """Formulario de alta/edicion de categorias."""

    class Meta:
        model = Category
        fields = ["name", "parent", "description"]


class BrandForm(forms.ModelForm):
    """Formulario de alta/edicion de marcas."""

    class Meta:
        model = Brand
        fields = ["name"]


class UnitForm(forms.ModelForm):
    """Formulario de alta/edicion de unidades de medida."""

    class Meta:
        model = UnitOfMeasure
        fields = ["code", "name"]


class ProductForm(forms.ModelForm):
    """Formulario de alta/edicion de productos."""

    class Meta:
        model = Product
        fields = [
            "sku",
            "barcode",
            "name",
            "description",
            "category",
            "brand",
            "uom",
            "sale_price",
            "min_stock",
            "max_stock",
            "reorder_point",
            "track_lots",
            "track_expiry",
            "rotation_strategy",
            "is_active",
        ]

    def clean(self):
        """Valida que ``track_expiry`` requiera ``track_lots``."""
        cleaned = super().clean()
        if cleaned.get("track_expiry") and not cleaned.get("track_lots"):
            self.add_error(
                "track_expiry",
                "Requiere que 'track_lots' este activo.",
            )
        return cleaned


__all__ = [
    "CategoryForm",
    "BrandForm",
    "UnitForm",
    "ProductForm",
]
