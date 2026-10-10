"""Tests de vistas de warehouses."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.warehouses.services import create_warehouse



@pytest.fixture
def warehouse(db):
    """Crea un almacen de prueba."""
    return create_warehouse(code="VX", name="ViewTest")


@pytest.mark.django_db
def test_warehouse_list_renders(admin_client, warehouse) -> None:
    """La lista de almacenes carga."""
    response = admin_client.get(reverse("warehouses:warehouse-list"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_warehouse_create_view_renders(admin_client) -> None:
    """El formulario de alta carga."""
    response = admin_client.get(reverse("warehouses:warehouse-create"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_warehouse_update_view_renders(admin_client, warehouse) -> None:
    """El formulario de edicion carga."""
    response = admin_client.get(
        reverse("warehouses:warehouse-update", args=[warehouse.pk])
    )
    assert response.status_code == 200
