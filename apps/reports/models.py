"""Modelo anclado a permisos custom para ``reports``.

Modelo ``managed=False`` que sirve solo para registrar permisos en
``auth.permission``. No tiene tabla asociada.
"""

from __future__ import annotations

from django.db import models


class ReportPermission(models.Model):
    """Modelo ancla para los permisos de la app ``reports``."""

    class Meta:
        managed = False
        default_permissions: tuple[str, ...] = ()
        verbose_name = "Permiso de reporte"
        verbose_name_plural = "Permisos de reporte"
        permissions = (
            ("view_reports", "Puede consultar reportes y dashboard"),
        )


__all__ = ["ReportPermission"]
