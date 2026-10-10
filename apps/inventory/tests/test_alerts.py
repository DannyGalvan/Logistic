"""Tests de ``AlertService`` y selectors de inventario."""

from __future__ import annotations

import datetime
from decimal import Decimal

import pytest

from apps.catalog.models import Brand, Category, Product, UnitOfMeasure
from apps.inventory.models import Alert, Lot
from apps.inventory.selectors import (
    expiring_lots,
    kardex,
    stock_by_product,
    stock_on_hand,
)
from apps.inventory.services import AlertService, InventoryService
from apps.warehouses.services import create_warehouse


@pytest.fixture
def setup(admin_user):
    """Crea producto y almacen."""
    cat = Category.objects.create(name="G")
    brand = Brand.objects.create(name="B")
    uom = UnitOfMeasure.objects.create(code="UND", name="Unidad")
    product = Product.objects.create(
        sku="P-200", name="Prod", category=cat, uom=uom, brand=brand,
        track_lots=False,
    )
    warehouse = create_warehouse(code="CEN", name="Central")
    location = warehouse.locations.filter(code="ALM-01").first()
    return {"user": admin_user, "product": product, "warehouse": warehouse, "location": location}


@pytest.mark.django_db
def test_alert_low_stock_resolves(setup) -> None:
    """``AlertService`` resuelve la alerta cuando el stock sube."""
    setup["product"].reorder_point = Decimal("5")
    setup["product"].save()
    InventoryService().receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("2"), unit_cost=Decimal("1"), user=setup["user"],
    )
    AlertService().evaluate_product(setup["product"])
    assert Alert.objects.filter(
        product=setup["product"], alert_type="LOW_STOCK"
    ).exists()
    InventoryService().receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("20"), unit_cost=Decimal("1"), user=setup["user"],
    )
    AlertService().evaluate_product(setup["product"])
    active = Alert.objects.filter(
        product=setup["product"], alert_type="LOW_STOCK",
        resolved_at__isnull=True,
    )
    assert not active.exists()


@pytest.mark.django_db
def test_alert_evaluate_expirations_creates_alerts(setup) -> None:
    """``evaluate_expirations`` crea alerta para lote expirado."""
    lot = Lot.objects.create(
        product=setup["product"],
        lot_number="L-EXPIRED",
        expires_at=datetime.date.today() - datetime.timedelta(days=5),
    )
    AlertService().evaluate_expirations()
    assert Alert.objects.filter(lot=lot, alert_type="EXPIRED").exists()


@pytest.mark.django_db
def test_stock_by_product_returns_rows(setup) -> None:
    """``stock_by_product`` devuelve las existencias."""
    InventoryService().receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("10"), unit_cost=Decimal("1"), user=setup["user"],
    )
    rows = list(stock_by_product(setup["product"]))
    assert rows


@pytest.mark.django_db
def test_stock_on_hand_returns_sum(setup) -> None:
    """``stock_on_hand`` suma las cantidades."""
    InventoryService().receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("15"), unit_cost=Decimal("1"), user=setup["user"],
    )
    assert stock_on_hand(setup["product"]) == Decimal("15.000")


@pytest.mark.django_db
def test_expiring_lots_returns_queryset(setup) -> None:
    """``expiring_lots`` devuelve un QuerySet."""
    qs = expiring_lots(days=365)
    assert qs is not None


@pytest.mark.django_db
def test_kardex_returns_rows(setup) -> None:
    """``kardex`` devuelve filas valorizadas."""
    InventoryService().receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("5"), unit_cost=Decimal("3"), user=setup["user"],
    )
    rows = kardex(setup["product"])
    assert rows


@pytest.mark.django_db
def test_movements_raise_and_resolve_low_stock_alert(setup) -> None:
    """Los movimientos disparan ``stock_changed`` y evaluan alertas solas."""
    product = setup["product"]
    product.reorder_point = Decimal("5")
    product.save()
    service = InventoryService()
    service.receive(product=product, location=setup["location"],
                    quantity=Decimal("10"), unit_cost=Decimal("1"), user=setup["user"])
    active = Alert.objects.filter(product=product, alert_type="LOW_STOCK",
                                  resolved_at__isnull=True)
    assert not active.exists()
    service.issue(product=product, location=setup["location"],
                  quantity=Decimal("8"), user=setup["user"])
    assert active.exists()
    service.receive(product=product, location=setup["location"],
                    quantity=Decimal("10"), unit_cost=Decimal("1"), user=setup["user"])
    assert not active.exists()
