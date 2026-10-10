"""Tests de selectors de sales."""

from __future__ import annotations

import datetime
from decimal import Decimal

import pytest

from apps.catalog.models import Brand, Category, Product, UnitOfMeasure
from apps.inventory.services import InventoryService
from apps.partners.services import create_customer
from apps.sales.selectors import orders, shipments
from apps.sales.services import SalesService
from apps.warehouses.services import create_warehouse


@pytest.fixture
def setup(admin_user):
    """Crea cliente, producto, almacen y ordenes."""
    cat = Category.objects.create(name="G")
    brand = Brand.objects.create(name="B")
    uom = UnitOfMeasure.objects.create(code="UND", name="Unidad")
    product = Product.objects.create(
        sku="P-S", name="Prod", category=cat, uom=uom, brand=brand,
    )
    warehouse = create_warehouse(code="CEN", name="Central")
    location = warehouse.locations.filter(code="ALM-01").first()
    customer = create_customer(name="Cust", tax_id="T-1")
    inventory = InventoryService()
    inventory.receive(
        product=product, location=location,
        quantity=Decimal("20"), unit_cost=Decimal("1"), user=admin_user,
    )
    service = SalesService()
    order = service.create_order(
        customer=customer, warehouse=warehouse,
        order_date=datetime.date.today(), user=admin_user,
    )
    service.add_line(order, product=product,
                     quantity=Decimal("2"), unit_price=Decimal("5"))
    return {
        "product": product, "warehouse": warehouse, "location": location,
        "customer": customer, "order": order,
    }


@pytest.mark.django_db
def test_orders_returns_queryset(setup) -> None:
    """``orders`` devuelve un QuerySet."""
    qs = orders()
    assert qs.count() >= 1


@pytest.mark.django_db
def test_orders_filtered(setup) -> None:
    """``orders`` acepta filtros."""
    qs = orders(filters={"customer": setup["customer"]})
    assert qs.count() == 1


@pytest.mark.django_db
def test_shipments_returns_queryset(setup) -> None:
    """``shipments`` devuelve un QuerySet."""
    qs = shipments()
    assert qs is not None
