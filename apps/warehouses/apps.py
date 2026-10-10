"""Configuracion de la app ``warehouses``."""

from __future__ import annotations

from django.apps import AppConfig

from apps.core.menu import MenuItem, MenuRegistry


class WarehousesConfig(AppConfig):
    """Configuracion de la app ``warehouses``."""

    name = "apps.warehouses"
    label = "warehouses"
    verbose_name = "Almacenes"

    def ready(self) -> None:
        """Registra el item del menu Almacenes."""
        registry = MenuRegistry()
        registry.register(
            MenuItem(
                label="Almacenes",
                url_name="warehouses:warehouse-list",
                icon="bi-building",
                permission="warehouse.view_warehouse",
                section="Almacenes",
                order=10,
            )
        )
