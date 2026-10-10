"""Configuracion de la app ``catalog``."""

from __future__ import annotations

from django.apps import AppConfig

from apps.core.menu import MenuItem, MenuRegistry


class CatalogConfig(AppConfig):
    """Configuracion de la app ``catalog``."""

    name = "apps.catalog"
    label = "catalog"
    verbose_name = "Catalogo"

    def ready(self) -> None:
        """Registra items del menu lateral."""
        registry = MenuRegistry()
        registry.register_many([
            MenuItem(
                label="Productos",
                url_name="catalog:product-list",
                icon="bi-box-seam",
                permission="catalog.view_product",
                section="Catalogo",
                order=10,
            ),
            MenuItem(
                label="Categorias",
                url_name="catalog:category-list",
                icon="bi-tags",
                permission="catalog.view_category",
                section="Catalogo",
                order=20,
            ),
            MenuItem(
                label="Marcas",
                url_name="catalog:brand-list",
                icon="bi-award",
                permission="catalog.view_brand",
                section="Catalogo",
                order=30,
            ),
            MenuItem(
                label="Unidades",
                url_name="catalog:unit-list",
                icon="bi-rulers",
                permission="catalog.view_unitofmeasure",
                section="Catalogo",
                order=40,
            ),
        ])
