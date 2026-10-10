"""Configuracion de la app ``core``."""

from __future__ import annotations

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuracion de la app ``core``.

    Atributos:
        name (str): Ruta Python canonica de la app.
        label (str): Etiqueta corta usada en ``apps.core_*``.
    """

    name = "apps.core"
    label = "core"
    verbose_name = "Nucleo"

    def ready(self) -> None:
        """Registra handlers y validadores al iniciar Django.

        Por ahora es un gancho vacio; las apps de dominio lo
        aprovecharan para registrar menus y auditoria.
        """
