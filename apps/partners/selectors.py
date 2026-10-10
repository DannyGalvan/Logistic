"""Selectors de la app ``partners``."""

from __future__ import annotations

from django.db.models import QuerySet

from .models import Customer, Supplier


def active_suppliers() -> QuerySet[Supplier]:
    """Devuelve proveedores activos."""
    return Supplier.active.all()


def active_customers() -> QuerySet[Customer]:
    """Devuelve clientes activos."""
    return Customer.active.all()


__all__ = ["active_suppliers", "active_customers"]
