"""Tests de estrategias FIFO / FEFO."""

from __future__ import annotations

import datetime
from decimal import Decimal

import pytest

from apps.catalog.models import Brand, Category, Product, UnitOfMeasure
from apps.core.exceptions import InsufficientStockError
from apps.inventory.models import Lot
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


@pytest.mark.django_db
def test_fefo_orders_by_expiry_and_skips_expired_and_quarantine(setup) -> None:
    """FEFO: primero el lote que vence antes; ignora vencidos y cuarentena."""
    product = setup["product"]
    product.track_lots = True
    product.track_expiry = True
    product.save()
    today = datetime.date.today()
    service = InventoryService()
    storage = setup["location"]
    quarantine = setup["warehouse"].locations.get(code="CUA")
    for number, days, location in (
        ("LATE", 90, storage), ("SOON", 10, storage),
        ("EXPIRED", -1, storage), ("QUAR", 5, quarantine),
    ):
        service.receive(
            product=product, location=location, quantity=Decimal("5"),
            unit_cost=Decimal("1"), user=setup["user"], lot_number=number,
            expires_at=today + datetime.timedelta(days=days),
        )
    allocations = FEFOStrategy().allocate(product, setup["warehouse"], Decimal("7"))
    lots = [Lot.objects.get(pk=a.lot_id).lot_number for a in allocations]
    assert lots == ["SOON", "LATE"]
    # Disponible: 100 sin lote (fixture) + SOON + LATE; vencido y cuarentena no cuentan.
    with pytest.raises(InsufficientStockError):
        FEFOStrategy().allocate(product, setup["warehouse"], Decimal("111"))
