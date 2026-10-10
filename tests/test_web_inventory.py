"""Formularios web de movimientos de inventario."""

from __future__ import annotations

import datetime
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.roles import Role
from apps.inventory.models import Lot
from apps.inventory.selectors import stock_on_hand

pytestmark = pytest.mark.django_db


@pytest.fixture
def keeper(client_as):
    """Cliente con rol Almacenista."""
    return client_as(Role.WAREHOUSE)


@pytest.fixture
def locations(warehouse_with_locations):
    """Ubicaciones ``ALM-01`` y ``DES``."""
    locs = warehouse_with_locations.locations
    return locs.get(code="ALM-01"), locs.get(code="DES")


def _receive(keeper, warehouse, location, product, quantity="10", **extra):
    """POST al formulario de entrada."""
    return keeper.post(reverse("inventory:receive"), {
        "warehouse": warehouse.pk, "location": location.pk, "product": product.pk,
        "quantity": quantity, "unit_cost": "2", **extra,
    })


def test_receive_issue_transfer_adjust(
    keeper, warehouse_with_locations, locations, product_factory,
) -> None:
    """Los cuatro formularios registran movimientos via service."""
    storage, shipping = locations
    product = product_factory()
    response = _receive(keeper, warehouse_with_locations, storage, product)
    assert response.status_code == 302
    keeper.post(reverse("inventory:issue"), {
        "location": storage.pk, "product": product.pk, "quantity": "2",
    })
    keeper.post(reverse("inventory:transfer"), {
        "location": storage.pk, "to_location": shipping.pk,
        "product": product.pk, "quantity": "3",
    })
    keeper.post(reverse("inventory:adjust"), {
        "location": shipping.pk, "product": product.pk, "counted_quantity": "1",
        "reference": "conteo rapido",
    })
    assert stock_on_hand(product) == Decimal("6")


def test_lot_tracked_product_requires_and_uses_lot(
    keeper, warehouse_with_locations, locations, product_factory,
) -> None:
    """Sin lote la entrada falla con error de formulario; con lote se usa."""
    storage, _ = locations
    product = product_factory(track_lots=True, track_expiry=True)
    missing = _receive(keeper, warehouse_with_locations, storage, product)
    assert missing.status_code == 200
    assert "requiere numero de lote" in str(missing.context["form"].non_field_errors())
    _receive(keeper, warehouse_with_locations, storage, product, lot_number="L1",
             expires_at=(datetime.date.today() + datetime.timedelta(days=90)).isoformat())
    lot = Lot.objects.get(lot_number="L1")
    keeper.post(reverse("inventory:issue"), {
        "location": storage.pk, "product": product.pk, "quantity": "4", "lot": lot.pk,
    })
    assert stock_on_hand(product) == Decimal("6")


def test_movement_form_errors(
    keeper, warehouse_with_locations, locations, product_factory,
) -> None:
    """Cantidad <= 0, misma ubicacion y stock insuficiente no generan 500."""
    storage, _ = locations
    product = product_factory()
    zero = _receive(keeper, warehouse_with_locations, storage, product, quantity="0")
    assert "quantity" in zero.context["form"].errors
    same = keeper.post(reverse("inventory:transfer"), {
        "location": storage.pk, "to_location": storage.pk,
        "product": product.pk, "quantity": "1",
    })
    assert "to_location" in same.context["form"].errors
    short = keeper.post(reverse("inventory:issue"), {
        "location": storage.pk, "product": product.pk, "quantity": "5",
    })
    assert short.status_code == 200
    assert short.context["form"].non_field_errors()


def test_inventory_lists_render(
    keeper, warehouse_with_locations, locations, product_factory,
) -> None:
    """Listas de stock, movimientos, lotes y alertas cargan con datos."""
    storage, _ = locations
    product = product_factory(reorder_point=Decimal("50"))
    _receive(keeper, warehouse_with_locations, storage, product)
    for name in ("stock-list", "movement-list", "lot-list", "alert-list"):
        assert keeper.get(reverse(f"inventory:{name}")).status_code == 200
