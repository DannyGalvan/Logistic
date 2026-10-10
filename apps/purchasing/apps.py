"""Configuracion de la app ``purchasing``."""

from __future__ import annotations

from django.apps import AppConfig

from apps.core.menu import MenuItem, MenuRegistry


class PurchasingConfig(AppConfig):
    """Configuracion de la app ``purchasing``."""

    name = "apps.purchasing"
    label = "purchasing"
    verbose_name = "Compras"

    def ready(self) -> None:
        """Registra el item de menu Compras."""
        registry = MenuRegistry()
        registry.register(
            MenuItem(
                label="Ordenes de compra",
                url_name="purchasing:order-list",
                icon="bi-cart-check",
                permission="purchasing.view_purchaseorder",
                section="Compras",
                order=10,
            )
        )
