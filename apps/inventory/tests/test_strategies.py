"""Tests de estrategias FIFO / FEFO."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.catalog.models import Brand, Category, Product, UnitOfMeasure
from apps.core.exceptions import InsufficientStockError
from apps.inventory.services import InventoryService
from apps.inventory.services.strategies import (
    FEFOStrategy,
    FIFOStrategy,
    get_strategy,
)
from apps.warehouses.services import create_warehouse


@pytest.fixture
def setup(admin_user):
    """Crea producto, almacen y stock base."""
    cat = Category.objects.create(name="G")
    brand = Brand.objects.create(name="B")
    uom = UnitOfMeasure.objects.create(code="UND", name="Unidad")
    product = Product.objects.create(
        sku="P-100", name="Prod", category=cat, uom=uom, brand=brand,
        track_lots=False,
    )
    warehouse = create_warehouse(code="CEN", name="Central")
    location = warehouse.locations.filter(code="ALM-01").first()
    InventoryService().receive(
        product=product, location=location,
        quantity=Decimal("100"), unit_cost=Decimal("5"), user=admin_user,
    )
    return {"user": admin_user, "product": product, "warehouse": warehouse, "location": location}


@pytest.mark.django_db
def test_fifo_strategy_returns_allocations(setup) -> None:
    """FIFO devuelve allocations para una cantidad."""
    allocations = FIFOStrategy().allocate(
        setup["product"], setup["warehouse"], Decimal("10"),
    )
    assert allocations
    assert sum(int(a.quantity) for a in allocations) == 10


@pytest.mark.django_db
def test_fefo_strategy_returns_allocations(setup) -> None:
    """FEFO devuelve allocations."""
    allocations = FEFOStrategy().allocate(
        setup["product"], setup["warehouse"], Decimal("5"),
    )
    assert allocations


@pytest.mark.django_db
def test_strategy_insufficient_stock(setup) -> None:
    """La estrategia lanza ``InsufficientStockError`` si no alcanza."""
    with pytest.raises(InsufficientStockError):
        FIFOStrategy().allocate(
            setup["product"], setup["warehouse"], Decimal("1000"),
        )


def test_get_strategy_returns_default() -> None:
    """``get_strategy`` con clave desconocida devuelve FIFO."""
    assert isinstance(get_strategy("UNKNOWN"), FIFOStrategy)
