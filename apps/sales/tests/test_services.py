"""Tests de servicios de sales."""

from __future__ import annotations

import datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.catalog.models import Brand, Category, Product, UnitOfMeasure
from apps.inventory.services import InventoryService
from apps.partners.services import create_customer
from apps.sales.services import SalesService, ShipLineInput
from apps.warehouses import services as warehouse_services


@pytest.fixture
def setup(db):
    """Crea cliente, producto y almacen con stock."""
    cat = Category.objects.create(name="General")
    brand = Brand.objects.create(name="Acme")
    uom = UnitOfMeasure.objects.create(code="UND", name="Unidad")
    product = Product.objects.create(
        sku="P-001", name="Prod", category=cat, uom=uom, brand=brand,
    )
    warehouse = warehouse_services.create_warehouse(code="CEN", name="Central")
    location = warehouse.locations.filter(code="ALM-01").first()
    customer = create_customer(name="Cust", tax_id="C-1")
    return {
        "product": product, "warehouse": warehouse,
        "location": location, "customer": customer,
    }


@pytest.fixture
def user(db):
    """Crea usuario de prueba."""
    return get_user_model().objects.create_user(
        username="tester", password="x1234567"
    )


@pytest.mark.django_db
def test_sales_order_full_flow(setup, user) -> None:
    """Crea, confirma y despacha la OV."""
    inv = InventoryService()
    inv.receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("20"), unit_cost=Decimal("1"), user=user,
    )
    svc = SalesService()
    order = svc.create_order(
        customer=setup["customer"], warehouse=setup["warehouse"],
        order_date=datetime.date.today(), user=user,
    )
    line = svc.add_line(
        order, product=setup["product"],
        quantity=Decimal("5"), unit_price=Decimal("2"),
    )
    svc.confirm(order)
    shipment = svc.ship(
        order,
        lines=[
            ShipLineInput(
                order_line_id=line.pk,
                location_id=setup["location"].pk,
                lot_id=None,
                quantity=Decimal("5"),
            )
        ],
        user=user,
    )
    order.refresh_from_db()
    assert order.status == "SHIPPED"
    assert shipment.lines.count() == 1


@pytest.mark.django_db
def test_ship_partial_keeps_order_partial(setup, user) -> None:
    """Despacho parcial deja la orden en ``PARTIALLY_SHIPPED``."""
    inv = InventoryService()
    inv.receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("10"), unit_cost=Decimal("1"), user=user,
    )
    svc = SalesService()
    order = svc.create_order(
        customer=setup["customer"], warehouse=setup["warehouse"],
        order_date=datetime.date.today(), user=user,
    )
    line = svc.add_line(
        order, product=setup["product"],
        quantity=Decimal("10"), unit_price=Decimal("2"),
    )
    svc.confirm(order)
    svc.ship(
        order,
        lines=[
            ShipLineInput(
                order_line_id=line.pk,
                location_id=setup["location"].pk,
                lot_id=None,
                quantity=Decimal("4"),
            )
        ],
        user=user,
    )
    order.refresh_from_db()
    assert order.status == "PARTIALLY_SHIPPED"


@pytest.mark.django_db
def test_ship_over_pending_fails(setup, user) -> None:
    """Despachar mas de lo pendiente falla."""
    inv = InventoryService()
    inv.receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("5"), unit_cost=Decimal("1"), user=user,
    )
    svc = SalesService()
    order = svc.create_order(
        customer=setup["customer"], warehouse=setup["warehouse"],
        order_date=datetime.date.today(), user=user,
    )
    line = svc.add_line(
        order, product=setup["product"],
        quantity=Decimal("3"), unit_price=Decimal("1"),
    )
    svc.confirm(order)
    with pytest.raises(ValidationError):
        svc.ship(
            order,
            lines=[
                ShipLineInput(
                    order_line_id=line.pk,
                    location_id=setup["location"].pk,
                    lot_id=None,
                    quantity=Decimal("10"),
                )
            ],
            user=user,
        )


@pytest.mark.django_db
def test_suggest_picking_returns_allocations(setup, user) -> None:
    """``suggest_picking`` devuelve allocations consistentes."""
    inv = InventoryService()
    inv.receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("20"), unit_cost=Decimal("1"), user=user,
    )
    svc = SalesService()
    order = svc.create_order(
        customer=setup["customer"], warehouse=setup["warehouse"],
        order_date=datetime.date.today(), user=user,
    )
    svc.add_line(
        order, product=setup["product"],
        quantity=Decimal("5"), unit_price=Decimal("2"),
    )
    suggestions = svc.suggest_picking(order)
    total = sum(int(s["quantity"]) for s in suggestions)
    assert total == 5
