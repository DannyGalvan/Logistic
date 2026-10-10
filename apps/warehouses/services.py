"""Servicios de la app ``warehouses``.

Operaciones de escritura para ``Warehouse`` y ``Location``.
``create_warehouse`` ademas genera las ubicaciones por defecto
(RECEIVING, STORAGE, SHIPPING, QUARANTINE) en una transaccion.
"""

from __future__ import annotations

from typing import Any

from django.db import transaction

from .models import Location, Warehouse


DEFAULT_LOCATIONS: list[tuple[str, str, str]] = [
    ("REC", "Recepcion", Location.LocationType.RECEIVING),
    ("ALM-01", "Almacenamiento", Location.LocationType.STORAGE),
    ("DES", "Despacho", Location.LocationType.SHIPPING),
    ("CUA", "Cuarentena", Location.LocationType.QUARANTINE),
]


@transaction.atomic
def create_warehouse(
    *,
    code: str,
    name: str,
    address: str = "",
    manager=None,
    is_active: bool = True,
    user=None,
) -> Warehouse:
    """Crea un almacen y sus ubicaciones por defecto."""
    warehouse = Warehouse.objects.create(
        code=code,
        name=name,
        address=address,
        manager=manager,
        is_active=is_active,
        created_by=user,
        updated_by=user,
    )
    for location_code, location_name, location_type in DEFAULT_LOCATIONS:
        Location.objects.create(
            warehouse=warehouse,
            code=location_code,
            name=location_name,
            location_type=location_type,
        )
    return warehouse


@transaction.atomic
def update_warehouse(warehouse: Warehouse, user=None, **fields: Any) -> Warehouse:
    """Actualiza un almacen."""
    for key, value in fields.items():
        setattr(warehouse, key, value)
    if user is not None:
        warehouse.updated_by = user
    warehouse.save()
    return warehouse


@transaction.atomic
def create_location(
    *,
    warehouse: Warehouse,
    code: str,
    name: str,
    location_type: str = Location.LocationType.STORAGE,
    is_active: bool = True,
) -> Location:
    """Crea una ubicacion en un almacen."""
    return Location.objects.create(
        warehouse=warehouse,
        code=code,
        name=name,
        location_type=location_type,
        is_active=is_active,
    )


@transaction.atomic
def update_location(location: Location, **fields: Any) -> Location:
    """Actualiza una ubicacion."""
    for key, value in fields.items():
        setattr(location, key, value)
    location.save()
    return location


@transaction.atomic
def deactivate_warehouse(warehouse: Warehouse, user=None) -> Warehouse:
    """Desactiva el almacen."""
    warehouse.is_active = False
    if user is not None:
        warehouse.updated_by = user
    warehouse.save(update_fields=["is_active", "updated_by", "updated_at"])
    return warehouse


__all__ = [
    "create_warehouse",
    "update_warehouse",
    "create_location",
    "update_location",
    "deactivate_warehouse",
    "DEFAULT_LOCATIONS",
]
