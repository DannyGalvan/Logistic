"""Modelos de la app ``partners``.

``Partner`` es abstracto. ``Supplier`` y ``Customer`` lo especializan
agregando campos propios.
"""

from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.core.managers import ActiveManager
from apps.core.models import (
    ActivatableModel,
    UserStampedModel,
)


class Partner(UserStampedModel, ActivatableModel):
    """Modelo abstracto base para proveedores y clientes."""

    name = models.CharField(max_length=120)
    tax_id = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    address = models.CharField(max_length=200, blank=True)
    contact_name = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self) -> str:
        """Devuelve el nombre del socio."""
        return self.name


class Supplier(Partner):
    """Proveedor."""

    lead_time_days = models.PositiveIntegerField(default=0)
    payment_terms = models.CharField(max_length=80, blank=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ["name"]


class Customer(Partner):
    """Cliente."""

    credit_limit = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=Decimal("0"),
        validators=[MinValueValidator(0)],
    )

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["name"]


__all__ = ["Supplier", "Customer"]
