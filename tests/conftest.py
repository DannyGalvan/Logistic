"""Fixtures compartidas por toda la suite de pruebas.

Por ahora solo expone la configuracion minima. Las fixtures `users_by_role`
y `client_as(role)` se completan en la Fase 2 cuando exista el modelo
``accounts.User`` con sus grupos.
"""

from __future__ import annotations

from typing import Iterator

import pytest
from django.contrib.auth import get_user_model
from django.test import Client


@pytest.fixture
def client_logged() -> Iterator[Client]:
    """Devuelve un cliente Django autenticado como superusuario.

    Yields:
        Cliente HTTP listo para emitir Peticiones autenticadas.
    """
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
