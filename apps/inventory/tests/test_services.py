"""Tests de los servicios de inventario."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.catalog.models import Brand, Category, Product, UnitOfMeasure
from apps.core.exceptions import (
    BusinessRuleError,
    InsufficientStockError,
)
from apps.inventory.models import Alert, Stock
from apps.inventory.services import AlertService, InventoryService
from apps.inventory.services.cycle_count_service import CycleCountService
from apps.warehouses import services as warehouse_services


@pytest.fixture
def setup(db):
    """Crea productos y almacenes de prueba."""
    cat = Category.objects.create(name="General")
    brand = Brand.objects.create(name="Acme")
    uom = UnitOfMeasure.objects.create(code="UND", name="Unidad")
    product = Product.objects.create(
        sku="P-001", name="Producto", category=cat, uom=uom, brand=brand,
        track_lots=False,
    )
    warehouse = warehouse_services.create_warehouse(code="CEN", name="Central")
    location = warehouse.locations.filter(code="ALM-01").first()
    return {
        "product": product,
        "warehouse": warehouse,
        "location": location,
        "category": cat,
        "uom": uom,
        "brand": brand,
    }


@pytest.fixture
def user(db):
    """Crea usuario de prueba."""
    return get_user_model().objects.create_user(
        username="tester", password="x1234567"
    )


@pytest.mark.django_db
def test_receive_creates_movement(setup, user) -> None:
    """La recepcion crea un movimiento y suma cantidad."""
    svc = InventoryService()
    movement = svc.receive(
        product=setup["product"],
        location=setup["location"],
        quantity=Decimal("10"),
        unit_cost=Decimal("5"),
        user=user,
    )
    assert movement.movement_type == "RECEIPT"
    assert movement.quantity == Decimal("10.000")


@pytest.mark.django_db
def test_issue_requires_sufficient_stock(setup, user) -> None:
    """La salida falla si no hay stock suficiente."""
    svc = InventoryService()
    with pytest.raises(InsufficientStockError):
        svc.issue(
            product=setup["product"],
            location=setup["location"],
            quantity=Decimal("1"),
            user=user,
        )


@pytest.mark.django_db
def test_issue_succeeds_after_receive(setup, user) -> None:
    """Tras recibir, una salida del mismo monto procede."""
    svc = InventoryService()
    svc.receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("10"), unit_cost=Decimal("5"), user=user,
    )
    svc.issue(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("3"), user=user,
    )
    stock = Stock.objects.get(
        product=setup["product"], location=setup["location"],
    )
    assert stock.quantity == Decimal("7.000")


@pytest.mark.django_db
def test_transfer_between_locations(setup, user) -> None:
    """La transferencia mueve stock entre dos ubicaciones."""
    dest = setup["warehouse"].locations.filter(code="DES").first()
    svc = InventoryService()
    svc.receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("20"), unit_cost=Decimal("1"), user=user,
    )
    svc.transfer(
        product=setup["product"],
        from_location=setup["location"],
        to_location=dest,
        quantity=Decimal("5"),
        user=user,
    )
    origin = Stock.objects.get(
        product=setup["product"], location=setup["location"],
    )
    target = Stock.objects.get(
        product=setup["product"], location=dest,
    )
    assert origin.quantity == Decimal("15.000")
    assert target.quantity == Decimal("5.000")


@pytest.mark.django_db
def test_transfer_same_location_fails(setup, user) -> None:
    """Transferir a la misma ubicacion lanza ``BusinessRuleError``."""
    svc = InventoryService()
    svc.receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("5"), unit_cost=Decimal("1"), user=user,
    )
    with pytest.raises(BusinessRuleError):
        svc.transfer(
            product=setup["product"],
            from_location=setup["location"],
            to_location=setup["location"],
            quantity=Decimal("1"),
            user=user,
        )


@pytest.mark.django_db
def test_adjust_with_zero_delta_returns_none(setup, user) -> None:
    """Ajustar a la misma cantidad existente devuelve ``None``."""
    svc = InventoryService()
    svc.receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("7"), unit_cost=Decimal("1"), user=user,
    )
    result = svc.adjust(
        product=setup["product"], location=setup["location"],
        counted_quantity=Decimal("7"), user=user,
    )
    assert result is None


@pytest.mark.django_db
def test_wac_updates_after_receive(setup, user) -> None:
    """El costo promedio ponderado se actualiza tras una recepcion."""
    svc = InventoryService()
    svc.receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("10"), unit_cost=Decimal("4"), user=user,
    )
    svc.receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("10"), unit_cost=Decimal("6"), user=user,
    )
    setup["product"].refresh_from_db()
    assert setup["product"].cost_price == Decimal("5.0000")


@pytest.mark.django_db
def test_wac_considers_stock_in_other_locations(setup, user) -> None:
    """El promedio usa la existencia total, no solo la de la ubicacion."""
    svc = InventoryService()
    svc.receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("30"), unit_cost=Decimal("4"), user=user,
    )
    other = setup["warehouse"].locations.exclude(pk=setup["location"].pk).first()
    svc.receive(
        product=setup["product"], location=other,
        quantity=Decimal("10"), unit_cost=Decimal("8"), user=user,
    )
    setup["product"].refresh_from_db()
    assert setup["product"].cost_price == Decimal("5.0000")


@pytest.mark.django_db
def test_cycle_count_full_flow(setup, user) -> None:
    """El ciclo de conteo completo: crear, iniciar, contar, aprobar."""
    svc_cycle = CycleCountService()
    svc_inv = InventoryService()
    svc_inv.receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("20"), unit_cost=Decimal("1"), user=user,
    )
    cycle = svc_cycle.create(
        warehouse=setup["warehouse"], user=user,
        location=setup["location"],
    )
    assert cycle.status == "DRAFT"
    svc_cycle.start(cycle)
    assert cycle.status == "IN_PROGRESS"
    line = cycle.lines.first()
    svc_cycle.record(line, Decimal("18"))
    svc_cycle.approve(cycle, user)
    cycle.refresh_from_db()
    assert cycle.status == "APPROVED"
    stock = Stock.objects.get(
        product=setup["product"], location=setup["location"],
    )
    assert stock.quantity == Decimal("18.000")


@pytest.mark.django_db
def test_alert_low_stock_creates_alert(setup, user) -> None:
    """``AlertService`` crea alerta cuando el stock esta bajo el minimo."""
    setup["product"].reorder_point = Decimal("5")
    setup["product"].save(update_fields=["reorder_point"])
    InventoryService().receive(
        product=setup["product"], location=setup["location"],
        quantity=Decimal("2"), unit_cost=Decimal("1"), user=user,
    )
    AlertService().evaluate_product(setup["product"])
    assert Alert.objects.filter(
        product=setup["product"], alert_type="LOW_STOCK",
    ).exists()
