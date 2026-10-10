"""Configuracion de la app ``quality``."""

from __future__ import annotations

from django.apps import AppConfig

from apps.core.menu import MenuItem, MenuRegistry


class QualityConfig(AppConfig):
    """Configuracion de la app ``quality``."""

    name = "apps.quality"
    label = "quality"
    verbose_name = "Calidad"

    def ready(self) -> None:
        """Registra item del menu Calidad."""
        registry = MenuRegistry()
        registry.register(
            MenuItem(
                label="Calidad",
                url_name="quality:dashboard",
                icon="bi-patch-check",
                permission="quality.view_lintrun",
                section="Calidad",
                order=10,
            )
        )
