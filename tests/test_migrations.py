"""Toda app propia con modelos debe tener migraciones.

``makemigrations --check`` ignora las apps sin carpeta ``migrations``;
en SQLite los tests las crean con ``syncdb`` y el fallo solo aparece en
Postgres/produccion (paso con ``audit`` y ``reports``).
"""

from __future__ import annotations

from importlib.util import find_spec

from django.apps import apps


def test_every_project_app_with_models_has_migrations() -> None:
    """Cada ``apps.*`` con modelos expone ``<app>.migrations``."""
    missing = [
        config.name
        for config in apps.get_app_configs()
        if config.name.startswith("apps.")
        and list(config.get_models())
        and find_spec(f"{config.name}.migrations") is None
    ]
    assert not missing, f"Apps sin migraciones: {missing}"
