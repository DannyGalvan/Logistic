"""Navegacion completa con cada rol sin errores 500 (DoD fase 8).

Carga ``seed_demo`` y recorre todas las URLs GET de la app (sin admin)
con un usuario de cada rol, rellenando los ``pk`` con objetos reales.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, override_settings
from django.urls import URLPattern, URLResolver, get_resolver, reverse

from apps.accounts.roles import Role
from apps.catalog.models import Brand, Category, Product, UnitOfMeasure
from apps.core.management.commands.seed_demo import DEMO_USERS
from apps.inventory.models import CycleCount
from apps.partners.models import Customer, Supplier
from apps.purchasing.models import PurchaseOrder
from apps.sales.models import SalesOrder
from apps.warehouses.models import Warehouse

SKIPPED_NAMESPACES = {"admin", "v1"}
POST_ONLY_SUFFIXES = (
    "-confirm", "-cancel", "-receive", "-ship", "-add-line", "-start",
    "-record", "-approve", "-deactivate",
)
POST_ONLY_NAMES = {"quality:run", "accounts:logout"}


def _pk_for(name: str) -> dict[str, int]:
    """Devuelve los kwargs de URL para ``name`` usando datos del seed."""
    by_prefix = {
        "catalog:category": Category,
        "catalog:brand": Brand,
        "catalog:unit": UnitOfMeasure,
        "catalog:product": Product,
        "warehouses:warehouse": Warehouse,
        "partners:supplier": Supplier,
        "partners:customer": Customer,
        "purchasing:order": PurchaseOrder,
        "sales:order": SalesOrder,
        "inventory:cycle-count": CycleCount,
        "accounts:user": get_user_model(),
    }
    if name == "warehouses:location-create":
        return {"warehouse_pk": Warehouse.objects.first().pk}
    for prefix, model in by_prefix.items():
        if name.startswith(prefix):
            obj = model.objects.order_by("pk").first()
            if name.endswith("-update") and hasattr(model, "Status"):
                obj = model.objects.filter(status="DRAFT").first()
            return {"pk": obj.pk}
    if name == "quality:run-detail":
        return {}
    raise AssertionError(f"Sin datos para {name}")


def _get_url_names() -> list[tuple[str, bool]]:
    """Lista ``(nombre, requiere_kwargs)`` de las URLs GET navegables."""
    names: list[tuple[str, bool]] = []

    def walk(resolver: URLResolver, namespace: str = "") -> None:
        for pattern in resolver.url_patterns:
            if isinstance(pattern, URLResolver):
                if pattern.namespace in SKIPPED_NAMESPACES:
                    continue
                child = f"{namespace}{pattern.namespace}:" if pattern.namespace else namespace
                walk(pattern, child)
            elif isinstance(pattern, URLPattern) and pattern.name:
                full = f"{namespace}{pattern.name}"
                if full in POST_ONLY_NAMES or full.endswith(POST_ONLY_SUFFIXES):
                    continue
                names.append((full, bool(pattern.pattern.converters)))

    walk(get_resolver())
    return names


@pytest.fixture
def seeded(db):  # noqa: ARG001
    """Base con datos demo."""
    with override_settings(DEBUG=True):
        call_command("seed_demo", verbosity=0)


@pytest.mark.django_db
@pytest.mark.parametrize("role", list(Role))
def test_every_page_renders_without_server_error(seeded, role) -> None:  # noqa: ARG001
    """Cada pagina responde 200/302/403 (nunca 500) para cada rol."""
    client = Client(raise_request_exception=True)
    client.force_login(get_user_model().objects.get(username=DEMO_USERS[role]))
    checked = 0
    for name, needs_kwargs in _get_url_names():
        kwargs = _pk_for(name) if needs_kwargs else {}
        if needs_kwargs and not kwargs:
            continue
        response = client.get(reverse(name, kwargs=kwargs))
        assert response.status_code in (200, 302, 403), (name, response.status_code)
        checked += 1
    assert checked > 40


@pytest.mark.django_db
def test_viewer_cannot_post_actions(seeded) -> None:  # noqa: ARG001
    """El rol Consulta recibe 403 en las acciones de escritura."""
    client = Client()
    client.force_login(get_user_model().objects.get(username=DEMO_USERS[Role.VIEWER]))
    order = PurchaseOrder.objects.filter(status="DRAFT").first()
    for name in ("purchasing:order-confirm", "purchasing:order-add-line"):
        assert client.post(reverse(name, args=[order.pk])).status_code == 403
    assert client.post(reverse("inventory:receive"), {}).status_code == 403


def test_swagger_lists_api(admin_client) -> None:
    """``/api/docs/`` y el esquema responden."""
    assert admin_client.get(reverse("swagger")).status_code == 200
    assert admin_client.get(reverse("schema")).status_code == 200
