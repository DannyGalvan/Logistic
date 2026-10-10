"""Tests de servicios y modelos del catalogo."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.catalog import services
from apps.catalog.models import Brand, Category, Product, UnitOfMeasure
from apps.catalog.selectors import search_products


@pytest.fixture
def category(db):
    """Categoria de prueba."""
    return Category.objects.create(name="Bebidas")


@pytest.fixture
def brand(db):
    """Marca de prueba."""
    return Brand.objects.create(name="Acme")


@pytest.fixture
def unit(db):
    """Unidad de prueba."""
    return UnitOfMeasure.objects.create(code="UND", name="Unidad")


@pytest.mark.django_db
def test_create_category_persists_record(category) -> None:
    """El servicio guarda la categoria con is_active=True."""
    assert category.is_active is True
    assert str(category) == "Bebidas"


@pytest.mark.django_db
def test_deactivate_category_sets_flag(category) -> None:
    """El servicio desactiva la categoria sin borrarla."""
    services.deactivate_category(category)
    category.refresh_from_db()
    assert category.is_active is False


@pytest.mark.django_db
def test_create_product_persists_record(category, brand, unit) -> None:
    """El service crea productos con todos los campos."""
    product = services.create_product(
        sku="P-001",
        name="Agua",
        category=category,
        uom=unit,
        brand=brand,
        sale_price=Decimal("5.50"),
    )
    assert product.sku == "P-001"
    assert product.is_active is True


@pytest.mark.django_db
def test_update_product_blocks_cost_price(category, brand, unit) -> None:
    """El service ignora cambios a ``cost_price``."""
    product = services.create_product(
        sku="P-002", name="X", category=category, uom=unit, brand=brand,
        cost_price=Decimal("10"),
    )
    services.update_product(product, cost_price=Decimal("999"))
    product.refresh_from_db()
    assert product.cost_price == Decimal("10.0000")


@pytest.mark.django_db
def test_product_track_expiry_requires_track_lots(category, brand, unit) -> None:
    """``track_expiry=True`` sin ``track_lots`` falla en ``clean()``."""
    product = Product(
        sku="P-003", name="Y", category=category, uom=unit,
        track_expiry=True,
    )
    with pytest.raises(ValidationError):
        product.clean()


@pytest.mark.django_db
def test_product_max_must_be_gte_min(category, brand, unit) -> None:
    """Crear un producto con max<min viola el check constraint."""
    with pytest.raises(IntegrityError):
        Product.objects.create(
            sku="P-004", name="Z", category=category, uom=unit,
            min_stock=Decimal("10"), max_stock=Decimal("5"),
        )


@pytest.mark.django_db
def test_search_products_finds_by_sku(category, brand, unit) -> None:
    """El selector busca por SKU (case-insensitive)."""
    services.create_product(
        sku="ABC-001", name="Prod1", category=category, uom=unit, brand=brand,
    )
    services.create_product(
        sku="DEF-002", name="Prod2", category=category, uom=unit, brand=brand,
    )
    results = list(search_products("abc"))
    assert any(p.sku == "ABC-001" for p in results)
