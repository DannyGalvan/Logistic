"""Configuracion de la app ``sales``."""

from __future__ import annotations

from django.apps import AppConfig

from apps.core.menu import MenuItem, MenuRegistry


class SalesConfig(AppConfig):
    """Configuracion de la app ``sales``."""

    name = "apps.sales"
    label = "sales"
    verbose_name = "Ventas"

    def ready(self) -> None:
        """Registra el item del menu Ventas."""
        registry = MenuRegistry()
        registry.register(
            MenuItem(
                label="Ordenes de venta",
                url_name="sales:order-list",
                icon="bi-receipt",
                permission="sales.view_salesorder",
                section="Ventas",
                order=10,
            )
        )
