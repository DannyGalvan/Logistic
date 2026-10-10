"""Configuracion de la app ``inventory``."""

from __future__ import annotations

from django.apps import AppConfig


class InventoryConfig(AppConfig):
    """Configuracion de la app ``inventory``."""

    name = "apps.inventory"
    label = "inventory"
    verbose_name = "Inventario"
