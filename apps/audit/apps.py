"""Configuracion de la app ``audit``."""

from __future__ import annotations

from django.apps import AppConfig

from apps.core.menu import MenuItem, MenuRegistry


class AuditConfig(AppConfig):
    """Configuracion de la app ``audit``."""

    name = "apps.audit"
    label = "audit"
    verbose_name = "Auditoria"

    def ready(self) -> None:
        """Registra el item de menu y conecta los handlers."""
        from . import registry, signals  # noqa: F401  pylint: disable=unused-import,import-outside-toplevel

        registry.register("catalog.Product", exclude_fields=["updated_at"])
        registry.register("catalog.Category", exclude_fields=["updated_at"])
        registry.register("warehouses.Warehouse", exclude_fields=["updated_at"])
        registry.register("partners.Supplier", exclude_fields=["updated_at"])
        registry.register("partners.Customer", exclude_fields=["updated_at"])
        registry_menu = MenuRegistry()
        registry_menu.register(
            MenuItem(
                label="Auditoria",
                url_name="audit:list",
                icon="bi-shield-check",
                permission="audit.view_auditlog",
                section="Administracion",
                order=30,
            )
        )
