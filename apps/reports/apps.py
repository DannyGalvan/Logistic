"""Configuracion de la app ``reports``."""

from __future__ import annotations

from django.apps import AppConfig

from apps.core.menu import MenuItem, MenuRegistry


class ReportsConfig(AppConfig):
    """Configuracion de la app ``reports``."""

    name = "apps.reports"
    label = "reports"
    verbose_name = "Reportes"

    def ready(self) -> None:
        """Registra item del menu Reportes."""
        registry = MenuRegistry()
        registry.register(
            MenuItem(
                label="Reportes",
                url_name="reports:dashboard",
                icon="bi-bar-chart",
                permission="reports.view_reports",
                section="Reportes",
                order=10,
            )
        )
