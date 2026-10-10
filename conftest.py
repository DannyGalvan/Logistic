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

from decimal import Decimal
from typing import Callable, Iterator

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient

from apps.accounts.roles import Role
from apps.accounts.services import assign_role


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
        user.save()
        assign_role(user, role)
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

@pytest.fixture
def warehouse_with_locations(db):  # noqa: ARG001
    """Almacen ``CEN`` con sus ubicaciones por defecto."""
    from apps.warehouses.services import create_warehouse

    return create_warehouse(code="CEN", name="Central")


@pytest.fixture
def product_factory(db) -> Callable[..., object]:  # noqa: ARG001
    """Factory de productos con categoria, marca y unidad compartidas."""
    from apps.catalog.models import Brand, Category, Product, UnitOfMeasure

    category, _ = Category.objects.get_or_create(name="General")
    brand, _ = Brand.objects.get_or_create(name="Generica")
    uom, _ = UnitOfMeasure.objects.get_or_create(code="UND", defaults={"name": "Unidad"})
    counter = {"n": 0}

    def factory(**overrides) -> Product:
        """Crea un producto con SKU unico; ``overrides`` ajusta campos."""
        counter["n"] += 1
        fields = {
            "sku": f"T-{counter['n']:04d}",
            "name": f"Producto test {counter['n']}",
            "category": category,
            "brand": brand,
            "uom": uom,
            "cost_price": Decimal("2.00"),
            "sale_price": Decimal("5.00"),
        }
        fields.update(overrides)
        return Product.objects.create(**fields)

    return factory
