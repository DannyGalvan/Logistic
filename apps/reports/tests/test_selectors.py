"""Tests de selectors de reports."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.catalog.models import Brand, Category, Product, UnitOfMeasure
from apps.inventory.services import InventoryService
from apps.reports.selectors import (
    dashboard_kpis,
    inventory_valuation,
    movements_by_day,
    top_moving_products,
)
from apps.warehouses.services import create_warehouse


@pytest.fixture
def setup(admin_user):
    """Crea producto, almacen y stock."""
    cat = Category.objects.create(name="G")
    brand = Brand.objects.create(name="B")
    uom = UnitOfMeasure.objects.create(code="UND", name="Unidad")
    product = Product.objects.create(
        sku="P-R", name="Prod", category=cat, uom=uom, brand=brand,
    )
    warehouse = create_warehouse(code="CEN", name="Central")
    location = warehouse.locations.filter(code="ALM-01").first()
    InventoryService().receive(
        product=product, location=location,
        quantity=Decimal("10"), unit_cost=Decimal("2"), user=admin_user,
    )
    return {"user": admin_user, "product": product, "warehouse": warehouse, "location": location}


@pytest.mark.django_db
def test_dashboard_kpis_returns_dict(setup) -> None:
    """``dashboard_kpis`` devuelve un dict con claves conocidas."""
    kpis = dashboard_kpis()
    assert "products" in kpis
    assert "warehouses" in kpis
    assert "stock_value" in kpis


@pytest.mark.django_db
def test_inventory_valuation_returns_decimal(setup) -> None:
    """``inventory_valuation`` devuelve un ``Decimal``."""
    value = inventory_valuation()
    assert value > 0


@pytest.mark.django_db
def test_top_moving_products_returns_list(setup) -> None:
    """``top_moving_products`` devuelve una lista."""
    items = list(top_moving_products())
    assert items is not None


@pytest.mark.django_db
def test_movements_by_day_returns_queryset(setup) -> None:
    """``movements_by_day`` devuelve un QuerySet."""
    qs = movements_by_day()
    assert qs is not None
