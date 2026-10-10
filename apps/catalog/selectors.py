"""Selectors de la app ``catalog``.

Funciones de lectura (querysets). Ninguna vista toca el manager
directamente.
"""

from __future__ import annotations

from django.db.models import Q, QuerySet

from .models import Brand, Category, Product, UnitOfMeasure


def search_products(term: str) -> QuerySet[Product]:
    """Busca productos por ``sku``, ``barcode`` o ``name``."""
    if not term:
        return Product.objects.none()
    return Product.objects.filter(
        Q(sku__icontains=term)
        | Q(barcode__icontains=term)
        | Q(name__icontains=term)
    )


def active_products() -> QuerySet[Product]:
    """Devuelve productos activos."""
    return Product.active.all()


def active_categories() -> QuerySet[Category]:
    """Devuelve categorias activas."""
    return Category.active.all()


def active_brands() -> QuerySet[Brand]:
    """Devuelve marcas activas."""
    return Brand.active.all()


def active_units() -> QuerySet[UnitOfMeasure]:
    """Devuelve unidades de medida activas."""
    return UnitOfMeasure.active.all()


__all__ = [
    "search_products",
    "active_products",
    "active_categories",
    "active_brands",
    "active_units",
]
