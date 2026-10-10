"""Tests de servicios de almacenes."""

from __future__ import annotations

from django.db import IntegrityError

import pytest

from apps.warehouses import services
from apps.warehouses.models import Location, Warehouse
from apps.warehouses.selectors import sellable_locations
from apps.warehouses.services import DEFAULT_LOCATIONS


@pytest.mark.django_db
def test_create_warehouse_creates_default_locations() -> None:
    """Al crear un almacen se generan las 4 ubicaciones por defecto."""
    warehouse = services.create_warehouse(code="CEN", name="Central")
    assert warehouse.code == "CEN"
    locations = list(warehouse.locations.all())
    assert len(locations) == len(DEFAULT_LOCATIONS)
    codes = {loc.code for loc in locations}
    expected_codes = {code for code, _, _ in DEFAULT_LOCATIONS}
    assert codes == expected_codes


@pytest.mark.django_db
def test_default_locations_include_quarantine() -> None:
    """Las ubicaciones por defecto incluyen cuarentena."""
    warehouse = services.create_warehouse(code="NOR", name="Norte")
    quarantine = Location.objects.get(
        warehouse=warehouse,
        location_type=Location.LocationType.QUARANTINE,
    )
    assert quarantine.is_active is True


@pytest.mark.django_db
def test_sellable_locations_excludes_quarantine() -> None:
    """``sellable_locations`` excluye cuarentena."""
    warehouse = services.create_warehouse(code="SUR", name="Sur")
    sellable = list(sellable_locations(warehouse))
    assert all(
        loc.location_type != Location.LocationType.QUARANTINE
        for loc in sellable
    )


@pytest.mark.django_db
def test_location_unique_per_warehouse() -> None:
    """Dos ubicaciones con el mismo codigo en el mismo almacen fallan."""
    warehouse = Warehouse.objects.create(code="X1", name="X1")
    Location.objects.create(warehouse=warehouse, code="A", name="A")
    with pytest.raises(IntegrityError):
        Location.objects.create(warehouse=warehouse, code="A", name="A2")


@pytest.mark.django_db
def test_deactivate_warehouse_does_not_delete() -> None:
    """Desactivar un almacen no lo borra."""
    warehouse = services.create_warehouse(code="T1", name="Test")
    services.deactivate_warehouse(warehouse)
    warehouse.refresh_from_db()
    assert warehouse.is_active is False
    assert Warehouse.objects.filter(pk=warehouse.pk).exists()
