"""Configuracion de la app ``accounts``."""

from __future__ import annotations

from django.apps import AppConfig

from apps.core.menu import MenuItem, MenuRegistry


class AccountsConfig(AppConfig):
    """Configuracion de la app ``accounts``.

    Registra los items del menu relacionados con la gestion de
    usuarios. El singleton ``MenuRegistry`` deduplica los items
    por ``url_name``, asi que es seguro llamar ``register`` cada vez
    que Django carga la app.
    """

    name = "apps.accounts"
    label = "accounts"
    verbose_name = "Cuentas"

    def ready(self) -> None:
        """Registra entradas del menu lateral al iniciar Django."""
        registry = MenuRegistry()
        registry.register_many([
            MenuItem(
                label="Perfil",
                url_name="accounts:profile",
                icon="bi-person-circle",
                section="Administracion",
                order=10,
            ),
            MenuItem(
                label="Usuarios",
                url_name="accounts:user-list",
                icon="bi-people",
                section="Administracion",
                permission="accounts.view_user",
                order=20,
            ),
        ])
