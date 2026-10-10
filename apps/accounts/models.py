"""Modelos de la app ``accounts``.

Incluye ``User`` con campos adicionales (``phone``, ``default_warehouse``)
y ``CustomPermissions``, un modelo ``managed=False`` que sirve de
anclaje para los permisos custom del sistema. Mantener un unico
modelo "permission carrier" evita que ``accounts`` dependa de apps
aun no implementadas (inventario, compras, ventas, etc.).
"""

from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models

from .roles import CUSTOM_PERMISSIONS


class User(AbstractUser):
    """Usuario del sistema con campos extra para StockFlow.

    Atributos adicionales:
        phone (str): Telefono de contacto (opcional).
        default_warehouse (Warehouse|None): Almacen predeterminado
            al iniciar sesi�n; se usa como filtro inicial en pantallas
            de inventario.
        role (str): Etiqueta legible del rol (sincronizada con
            ``Group`` mediante ``setup_roles``).
    """

    phone = models.CharField(max_length=32, blank=True)
    default_warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    role = models.CharField(max_length=32, blank=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["username"]

    def __str__(self) -> str:
        """Devuelve el username como representacion legible."""
        return self.username


class CustomPermissions(models.Model):
    """Modelo ``managed=False`` que registra permisos custom.

    No tiene tabla. Sirve para que ``Meta.permissions`` genere las
    entradas de ``auth.permission`` en las migraciones. Cada permiso
    custom del proyecto vive aqui en lugar de estar disperso en los
    modelos stub de otras apps.
    """

    class Meta:
        managed = False
        default_permissions: tuple[str, ...] = ()
        verbose_name = "Permisos custom"
        verbose_name_plural = "Permisos custom"
        permissions = list(CUSTOM_PERMISSIONS)


__all__ = ["User", "CustomPermissions"]
