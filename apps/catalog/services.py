"""Servicios de la app ``catalog``.

Operaciones de escritura (alta, edicion, desactivacion) para
``Category``, ``Brand``, ``UnitOfMeasure`` y ``Product``. Las vistas
delegan aqui; nunca tocan ``Model.objects`` directamente.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db import transaction

from .models import Brand, Category, Product, UnitOfMeasure


@transaction.atomic
def create_category(*, name: str, parent=None, description: str = "") -> Category:
    """Crea una categoria."""
    return Category.objects.create(
        name=name, parent=parent, description=description
    )


@transaction.atomic
def update_category(category: Category, **fields: Any) -> Category:
    """Actualiza una categoria."""
    for key, value in fields.items():
        setattr(category, key, value)
    category.save()
    return category


@transaction.atomic
def deactivate_category(category: Category) -> Category:
    """Desactiva una categoria."""
    category.is_active = False
    category.save(update_fields=["is_active", "updated_at"])
    return category


@transaction.atomic
def create_brand(*, name: str) -> Brand:
    """Crea una marca."""
    return Brand.objects.create(name=name)


@transaction.atomic
def create_unit(*, code: str, name: str) -> UnitOfMeasure:
    """Crea una unidad de medida."""
    return UnitOfMeasure.objects.create(code=code, name=name)


@transaction.atomic
def create_product(  # pylint: disable=too-many-arguments,too-many-locals
    *,
    sku: str,
    name: str,
    category: Category,
    uom: UnitOfMeasure,
    brand: Brand | None = None,
    barcode: str | None = None,
    description: str = "",
    cost_price: Decimal = Decimal("0"),
    sale_price: Decimal = Decimal("0"),
    min_stock: Decimal = Decimal("0"),
    max_stock: Decimal = Decimal("0"),
    reorder_point: Decimal = Decimal("0"),
    track_lots: bool = False,
    track_expiry: bool = False,
    rotation_strategy: str = "FIFO",
    is_active: bool = True,
    user=None,
) -> Product:  # pylint: disable=too-many-arguments,too-many-locals
    """Crea un producto."""
    product = Product.objects.create(
        sku=sku,
        barcode=barcode,
        name=name,
        description=description,
        category=category,
        brand=brand,
        uom=uom,
        cost_price=cost_price,
        sale_price=sale_price,
        min_stock=min_stock,
        max_stock=max_stock,
        reorder_point=reorder_point,
        track_lots=track_lots,
        track_expiry=track_expiry,
        rotation_strategy=rotation_strategy,
        is_active=is_active,
        created_by=user,
        updated_by=user,
    )
    return product


@transaction.atomic
def update_product(product: Product, user=None, **fields: Any) -> Product:
    """Actualiza un producto. No permite modificar ``cost_price``."""
    forbidden = {"cost_price"}
    for key, value in fields.items():
        if key in forbidden:
            continue
        setattr(product, key, value)
    if user is not None:
        product.updated_by = user
    product.save()
    return product


@transaction.atomic
def deactivate_product(product: Product, user=None) -> Product:
    """Desactiva un producto."""
    product.is_active = False
    if user is not None:
        product.updated_by = user
    product.save(update_fields=["is_active", "updated_by", "updated_at"])
    return product


__all__ = [
    "create_category",
    "update_category",
    "deactivate_category",
    "create_brand",
    "create_unit",
    "create_product",
    "update_product",
    "deactivate_product",
]
