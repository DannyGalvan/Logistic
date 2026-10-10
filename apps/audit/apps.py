"""Configuracion de la app ``audit``."""

from __future__ import annotations

from django.apps import AppConfig


class AuditConfig(AppConfig):
    """Configuracion de la app ``audit``."""

    name = "apps.audit"
    label = "audit"
    verbose_name = "Auditoria"
