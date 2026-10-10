"""Cuentas (perfil, CRUD con rol), filtros de plantilla y vistas base."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.template import Context, Template
from django.test import RequestFactory
from django.urls import reverse

from apps.accounts.roles import Role
from apps.accounts.services import assign_role
from apps.core.templatetags import ui
from apps.core.views import (
    BaseListView,
    error_403,
    error_404,
    error_500,
    error_text,
    form_errors_text,
    parse_date,
    parse_decimal,
)


@pytest.mark.django_db
def test_profile_update_and_password_change(client, django_user_model) -> None:
    """El usuario edita su perfil y cambia su contrasena."""
    user = django_user_model.objects.create_user(username="eva", password="Vieja-123")
    client.force_login(user)
    url = reverse("accounts:profile")
    assert client.get(url).status_code == 200
    client.post(url, {"action": "profile", "first_name": "Eva", "email": "eva@x.com"})
    user.refresh_from_db()
    assert user.first_name == "Eva"
    bad = client.post(url, {"action": "profile", "email": "no-es-correo"})
    assert bad.context["profile_form"].errors
    client.post(url, {
        "action": "password", "old_password": "Vieja-123",
        "new_password1": "Nueva-Segura-456", "new_password2": "Nueva-Segura-456",
    })
    user.refresh_from_db()
    assert user.check_password("Nueva-Segura-456")
    wrong = client.post(url, {"action": "password", "old_password": "x"})
    assert wrong.context["password_form"].errors


@pytest.mark.django_db
def test_user_create_and_update_sync_role_group(client_as, django_user_model) -> None:
    """Crear/editar usuario con rol lo deja en el grupo correcto."""
    admin = client_as(Role.ADMIN)
    admin.post(reverse("accounts:user-create"), {
        "username": "nuevo", "password1": "Clave-Segura-789",
        "password2": "Clave-Segura-789", "role": str(Role.SALES), "is_active": "on",
    })
    user = django_user_model.objects.get(username="nuevo")
    assert list(user.groups.values_list("name", flat=True)) == [str(Role.SALES)]
    admin.post(reverse("accounts:user-update", args=[user.pk]), {
        "username": "nuevo", "role": str(Role.VIEWER), "is_active": "on",
    })
    assert list(user.groups.values_list("name", flat=True)) == [str(Role.VIEWER)]
    assert user.has_perm("catalog.view_product")


@pytest.mark.django_db
def test_assign_role_empty_clears_groups(django_user_model) -> None:
    """Rol vacio quita los grupos."""
    user = django_user_model.objects.create_user(username="r", password="x")
    assign_role(user, Role.SALES)
    assign_role(user, "")
    assert user.role == ""
    assert not user.groups.exists()


def test_money_qty_and_badges() -> None:
    """Filtros de formato toleran valores invalidos."""
    assert ui.money("1234.5") == "Q1,234.50"
    assert ui.money("abc") == "-"
    assert ui.qty(Decimal("2")) == "2.000"
    assert ui.qty(None) == "-"
    assert ui.status_badge("SHIPPED") == "bg-success"
    assert ui.status_badge("???") == "bg-secondary"
    assert ui.status_soft("CANCELLED") == "badge-soft-danger"


def test_nav_active_without_request_or_unknown_path() -> None:
    """``nav_active`` no falla sin request ni con rutas desconocidas."""
    template = Template("{% load ui %}[{% nav_active 'core:dashboard' %}]")
    assert template.render(Context({})) == "[]"
    request = RequestFactory().get("/no-existe/")
    assert template.render(Context({"request": request})) == "[]"
    request = RequestFactory().get("/")
    assert template.render(Context({"request": request})) == "[active]"


def test_parsers_and_error_text() -> None:
    """Helpers de vistas."""
    assert parse_decimal("1.5") == Decimal("1.5")
    assert parse_decimal("x") is None
    assert parse_decimal("") is None
    assert parse_date("2026-01-02").day == 2
    assert parse_date("31-31-2026") is None
    assert error_text(ValidationError(["a", "b"])) == "a b"
    assert error_text(ValueError("x")) == "x"

    class _Form:
        errors = {"name": ["Requerido."]}

    assert form_errors_text(_Form()) == "name: Requerido."


def test_base_list_view_requires_queryset_hook() -> None:
    """``BaseListView`` exige implementar ``get_base_queryset``."""
    with pytest.raises(ImproperlyConfigured):
        BaseListView().get_queryset()


@pytest.mark.django_db
def test_error_handlers_render() -> None:
    """Las vistas de error responden con su codigo."""
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    assert error_403(request).status_code == 403
    assert error_404(request).status_code == 404
    assert error_500(request).status_code == 500
