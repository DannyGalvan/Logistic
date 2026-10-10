"""Configuracion de la app ``inventory``."""

from __future__ import annotations

from django.apps import AppConfig

from apps.core.menu import MenuItem, MenuRegistry


class InventoryConfig(AppConfig):
    """Configuracion de la app ``inventory``."""

    name = "apps.inventory"
    label = "inventory"
    verbose_name = "Inventario"

    def ready(self) -> None:
        """Registra items del menu Inventario y los signals."""
        registry = MenuRegistry()
        registry.register_many([
            MenuItem(
                label="Stock",
                url_name="inventory:stock-list",
                icon="bi-boxes",
                permission="inventory.view_stock",
                section="Inventario",
                order=10,
            ),
            MenuItem(
                label="Movimientos",
                url_name="inventory:movement-list",
                icon="bi-arrow-left-right",
                permission="inventory.view_movement",
                section="Inventario",
                order=20,
            ),
            MenuItem(
                label="Lotes",
                url_name="inventory:lot-list",
                icon="bi-tag",
                permission="inventory.view_stock",
                section="Inventario",
                order=30,
            ),
            MenuItem(
                label="Conteos",
                url_name="inventory:cycle-count-list",
                icon="bi-clipboard-check",
                permission="inventory.view_cyclecount",
                section="Inventario",
                order=40,
            ),
            MenuItem(
                label="Alertas",
                url_name="inventory:alert-list",
                icon="bi-bell",
                permission="inventory.view_alert",
                section="Inventario",
                order=50,
            ),
        ])
        # Registra receivers de ``stock_changed`` (efecto secundario).
        from . import signals  # noqa: F401  pylint: disable=import-outside-toplevel,unused-import
