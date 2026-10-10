"""Managers personalizados para modelos del nucleo."""

from __future__ import annotations

from django.db import models


class ActiveManager(models.Manager):
    """Manager que filtra registros con ``is_active=True``.

    Uso::

        class Producto(ActivatableModel):
            objects = models.Manager()
            active = ActiveManager()
    """

    def get_queryset(self) -> models.QuerySet:
        """Devuelve el queryset restringido a registros activos."""
        return super().get_queryset().filter(is_active=True)
