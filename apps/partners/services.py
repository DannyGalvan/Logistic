"""Servicios de la app ``partners``."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db import transaction

from .models import Customer, Supplier


@transaction.atomic
def create_supplier(*, user=None, **fields: Any) -> Supplier:
    """Crea un proveedor."""
    return Supplier.objects.create(created_by=user, updated_by=user, **fields)


@transaction.atomic
def update_supplier(supplier: Supplier, user=None, **fields: Any) -> Supplier:
    """Actualiza un proveedor."""
    for key, value in fields.items():
        setattr(supplier, key, value)
    if user is not None:
        supplier.updated_by = user
    supplier.save()
    return supplier


@transaction.atomic
def create_customer(*, user=None, **fields: Any) -> Customer:
    """Crea un cliente."""
    return Customer.objects.create(
        created_by=user,
        updated_by=user,
        credit_limit=fields.pop("credit_limit", Decimal("0")),
        **fields,
    )


@transaction.atomic
def update_customer(customer: Customer, user=None, **fields: Any) -> Customer:
    """Actualiza un cliente."""
    for key, value in fields.items():
        setattr(customer, key, value)
    if user is not None:
        customer.updated_by = user
    customer.save()
    return customer


__all__ = [
    "create_supplier",
    "update_supplier",
    "create_customer",
    "update_customer",
]
