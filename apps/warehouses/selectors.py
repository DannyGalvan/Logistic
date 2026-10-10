"""Selectors de la app ``warehouses``."""

from __future__ import annotations

from django.db.models import QuerySet

from .models import Location, Warehouse


def active_warehouses() -> QuerySet[Warehouse]:
    """Devuelve almacenes activos."""
    return Warehouse.active.all()


def locations_for(warehouse: Warehouse) -> QuerySet[Location]:
    """Devuelve las ubicaciones de un almacen."""
    return Location.objects.filter(warehouse=warehouse, is_active=True)


def sellable_locations(warehouse: Warehouse) -> QuerySet[Location]:
    """Devuelve ubicaciones activas y no cuarentena de un almacen."""
    return Location.objects.filter(
        warehouse=warehouse,
        is_active=True,
    ).exclude(location_type=Location.LocationType.QUARANTINE)


__all__ = [
    "active_warehouses",
    "locations_for",
    "sellable_locations",
]
