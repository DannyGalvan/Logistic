"""Modelos de la app ``warehouses``.

En la Fase 3 este archivo se reemplaza por el modelo ``Warehouse``
completo con `address`, `manager` y servicios. Por ahora expone un
stub minimo para que ``accounts.User.default_warehouse`` pueda
referenciarlo sin acoplar el orden de las migraciones.
"""

from __future__ import annotations

from django.db import models

from apps.core.models import (
    ActivatableModel,
    TimeStampedModel,
    UserStampedModel,
)


class Warehouse(UserStampedModel, ActivatableModel):
    """Almacen fisico donde se ubica el stock."""

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=200, blank=True)
    manager = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        verbose_name = "Almacen"
        verbose_name_plural = "Almacenes"
        ordering = ["code"]

    def __str__(self) -> str:
        """Devuelve ``codigo - nombre`` como representacion legible."""
        return f"{self.code} - {self.name}"


class Location(TimeStampedModel, ActivatableModel):
    """Ubicacion fisica dentro de un almacen."""

    class LocationType(models.TextChoices):
        """Tipo logico de la ubicacion fisica."""

        RECEIVING = "RECEIVING", "Recepcion"
        STORAGE = "STORAGE", "Almacenamiento"
        PICKING = "PICKING", "Picking"
        SHIPPING = "SHIPPING", "Despacho"
        QUARANTINE = "QUARANTINE", "Cuarentena"

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="locations",
    )
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=120)
    location_type = models.CharField(
        max_length=12,
        choices=LocationType.choices,
        default=LocationType.STORAGE,
    )

    class Meta:
        verbose_name = "Ubicacion"
        verbose_name_plural = "Ubicaciones"
        ordering = ["warehouse", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["warehouse", "code"],
                name="warehouses_location_unique_per_warehouse",
            )
        ]

    def __str__(self) -> str:
        """Devuelve ``almacen.codigo - ubicacion.codigo``."""
        return f"{self.warehouse.code}-{self.code}"


__all__ = ["Warehouse", "Location"]
