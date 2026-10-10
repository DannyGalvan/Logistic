"""Tests de servicios de purchasing."""

from __future__ import annotations

import datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.catalog.models import Brand, Category, Product, UnitOfMeasure
from apps.partners.services import create_supplier
from apps.purchasing.services import PurchaseService, ReceiptLineInput
from apps.warehouses import services as warehouse_services


@pytest.fixture
def setup(db):
    """Crea proveedores, productos y almacenes."""
    cat = Category.objects.create(name="General")
    brand = Brand.objects.create(name="Acme")
    uom = UnitOfMeasure.objects.create(code="UND", name="Unidad")
    product = Product.objects.create(
        sku="P-001", name="Prod", category=cat, uom=uom, brand=brand,
    )
    warehouse = warehouse_services.create_warehouse(code="CEN", name="Central")
    location = warehouse.locations.filter(code="ALM-01").first()
    supplier = create_supplier(name="Sup", tax_id="S-1")
    return {
        "product": product,
        "warehouse": warehouse,
        "location": location,
        "supplier": supplier,
    }


@pytest.fixture
def user(db):
    """Crea usuario de prueba."""
    return get_user_model().objects.create_user(
        username="tester", password="x1234567"
    )


@pytest.mark.django_db
def test_order_full_flow(setup, user) -> None:
    """Crea, confirma, recibe y verifica la OC."""
    svc = PurchaseService()
    order = svc.create_order(
        supplier=setup["supplier"],
        warehouse=setup["warehouse"],
        order_date=datetime.date.today(),
        user=user,
    )
    svc.add_line(
        order,
        product=setup["product"],
        quantity=Decimal("10"),
        unit_cost=Decimal("5"),
    )
    svc.confirm(order)
    assert order.status == "CONFIRMED"
    receipt = svc.receive(
        order,
        location=setup["location"],
        lines=[
            ReceiptLineInput(order_line_id=order.lines.first().pk,
                             quantity=Decimal("4"))
        ],
        user=user,
    )
    order.refresh_from_db()
    assert order.status == "PARTIALLY_RECEIVED"
    assert receipt.lines.count() == 1


@pytest.mark.django_db
def test_receive_full_completes_order(setup, user) -> None:
    """Recibir todo deja la orden en ``RECEIVED``."""
    svc = PurchaseService()
    order = svc.create_order(
        supplier=setup["supplier"], warehouse=setup["warehouse"],
        order_date=datetime.date.today(), user=user,
    )
    line = svc.add_line(
        order, product=setup["product"],
        quantity=Decimal("5"), unit_cost=Decimal("1"),
    )
    svc.confirm(order)
    svc.receive(
        order, location=setup["location"],
        lines=[ReceiptLineInput(order_line_id=line.pk, quantity=Decimal("5"))],
        user=user,
    )
    order.refresh_from_db()
    assert order.status == "RECEIVED"


@pytest.mark.django_db
def test_receive_over_pending_fails(setup, user) -> None:
    """Recibir mas de lo pendiente lanza ``ValidationError``."""
    svc = PurchaseService()
    order = svc.create_order(
        supplier=setup["supplier"], warehouse=setup["warehouse"],
        order_date=datetime.date.today(), user=user,
    )
    line = svc.add_line(
        order, product=setup["product"],
        quantity=Decimal("3"), unit_cost=Decimal("1"),
    )
    svc.confirm(order)
    with pytest.raises(ValidationError):
        svc.receive(
            order, location=setup["location"],
            lines=[
                ReceiptLineInput(order_line_id=line.pk, quantity=Decimal("5"))
            ],
            user=user,
        )


@pytest.mark.django_db
def test_confirm_without_lines_fails(setup) -> None:
    """Confirmar una orden sin lineas falla."""
    svc = PurchaseService()
    order = svc.create_order(
        supplier=setup["supplier"], warehouse=setup["warehouse"],
        order_date=datetime.date.today(),
    )
    with pytest.raises(ValidationError):
        svc.confirm(order)
