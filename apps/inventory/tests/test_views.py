"""Tests de vistas de inventory."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.inventory.services import InventoryService
from apps.catalog.models import Category, Product, UnitOfMeasure, Brand
from apps.warehouses.services import create_warehouse


@pytest.fixture
def setup(admin_user):
    """Crea datos minimos."""
    cat = Category.objects.create(name="G")
    brand = Brand.objects.create(name="B")
    uom = UnitOfMeasure.objects.create(code="UND", name="Unidad")
    product = Product.objects.create(
        sku="V-1", name="Prod", category=cat, uom=uom, brand=brand,
    )
    warehouse = create_warehouse(code="VX", name="ViewX")
    location = warehouse.locations.filter(code="ALM-01").first()
    InventoryService().receive(
        product=product, location=location,
        quantity=Decimal("5"),
        unit_cost=Decimal("1"), user=admin_user,
    )
    return {"user": admin_user, "product": product, "warehouse": warehouse, "location": location}



@pytest.mark.django_db
def test_stock_list_renders(admin_client, setup) -> None:
    """La lista de stock carga."""
    response = admin_client.get(reverse("inventory:stock-list"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_movement_list_renders(admin_client) -> None:
    """La lista de movimientos carga."""
    response = admin_client.get(reverse("inventory:movement-list"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_alert_list_renders(admin_client) -> None:
    """La lista de alertas carga."""
    response = admin_client.get(reverse("inventory:alert-list"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_cycle_count_list_renders(admin_client) -> None:
    """La lista de conteos carga."""
    response = admin_client.get(reverse("inventory:cycle-count-list"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_cycle_count_create_view_renders(admin_client) -> None:
    """El formulario de alta de conteo carga."""
    response = admin_client.get(reverse("inventory:cycle-count-create"))
    assert response.status_code == 200
