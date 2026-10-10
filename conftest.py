"""Fixtures compartidas por toda la suite de pruebas.

Incluye:

- ``client_logged``: cliente Django autenticado como superusuario.
- ``users_by_role``: crea un usuario por cada ``Role`` y los devuelve
  en un dict.
- ``client_as(role)``: factory que devuelve un cliente HTTP ya
  autenticado como el usuario de ese rol.
- ``api_client_as(role)``: equivalente usando ``APIClient`` de DRF.
"""

from __future__ import annotations

from typing import Callable, Iterator

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient

from apps.accounts.roles import Role


@pytest.fixture
def client_logged() -> Iterator[Client]:
    """Devuelve un cliente Django autenticado como superusuario."""
    user_model = get_user_model()
    user, _ = user_model.objects.get_or_create(
        username="tester",
        defaults={"is_staff": True, "is_superuser": True, "email": "t@example.com"},
    )
    user.set_password("test1234")
    user.save()
    client = Client()
    client.force_login(user)
    yield client


@pytest.fixture
def users_by_role(db) -> dict[Role, object]:  # noqa: ARG001
    """Crea un usuario por rol (incluye ``setup_roles`` automatico)."""
    from django.core.management import call_command

    call_command("setup_roles", verbosity=0)
    user_model = get_user_model()
    created: dict[Role, object] = {}
    for role in Role:
        username = f"user_{role.value.lower().replace(' ', '_')}"
        user, _ = user_model.objects.get_or_create(
            username=username,
            defaults={"email": f"{username}@example.com", "is_active": True},
        )
        user.set_password("test1234")
        user.role = str(role)
        user.save()
        created[role] = user
    return created


@pytest.fixture
def client_as(users_by_role) -> Callable[[Role], Client]:
    """Devuelve una factory que produce clientes autenticados por rol."""

    def factory(role: Role) -> Client:
        """Crea un nuevo ``Client`` ya autenticado para ``role``."""
        client = Client()
        client.force_login(users_by_role[role])
        return client

    return factory


@pytest.fixture
def api_client_as(users_by_role) -> Callable[[Role], APIClient]:
    """Devuelve una factory de ``APIClient`` autenticada por rol."""

    def factory(role: Role) -> APIClient:
        """Crea un ``APIClient`` autenticado como el usuario del rol."""
        client = APIClient()
        client.force_authenticate(users_by_role[role])
        return client

    return factory