"""Tests de ``accounts.roles`` y ``setup_roles``."""

from __future__ import annotations

from django.contrib.auth.models import Group, Permission
from django.core.management import call_command

import pytest

from apps.accounts.roles import (
    CUSTOM_PERMISSIONS,
    PERMISSIONS_BY_APP,
    ROLE_PERMISSIONS,
    Role,
)


def test_role_enum_has_all_expected_roles() -> None:
    """El enum ``Role`` incluye los seis roles del plan."""
    expected = {
        "ADMIN",
        "SUPERVISOR",
        "WAREHOUSE",
        "PURCHASING",
        "SALES",
        "VIEWER",
    }
    assert {r.name for r in Role} == expected


def test_role_permissions_cover_admin_for_all_apps() -> None:
    """El admin recibe todos los permisos listados por app."""
    admin_perms = set(ROLE_PERMISSIONS[Role.ADMIN])
    for app, codenames in PERMISSIONS_BY_APP.items():
        for codename in codenames:
            assert f"{app}.{codename}" in admin_perms


def test_role_permissions_are_distinct_per_role() -> None:
    """Ningun par de roles comparte exactamente la misma lista."""
    pairs: list[tuple[Role, str]] = []
    for role, codenames in ROLE_PERMISSIONS.items():
        pairs.append((role, ",".join(sorted(codenames))))
    signatures = [signature for _, signature in pairs]
    assert len(set(signatures)) == len(pairs)


def test_role_permissions_reference_known_apps() -> None:
    """Cada perm referencia una app de ``PERMISSIONS_BY_APP``."""
    known_apps = set(PERMISSIONS_BY_APP)
    for role, codenames in ROLE_PERMISSIONS.items():
        for codename in codenames:
            app = codename.split(".", 1)[0]
            assert app in known_apps, f"{role} referencia app desconocida {app}"


def test_custom_permissions_have_unique_codenames() -> None:
    """Los codenames custom son unicos."""
    codenames = [code for code, _ in CUSTOM_PERMISSIONS]
    assert len(set(codenames)) == len(codenames)


@pytest.mark.django_db
def test_setup_roles_creates_groups() -> None:
    """``setup_roles`` crea un grupo por cada rol."""
    call_command("setup_roles", verbosity=0)
    assert Group.objects.count() == len(Role)


@pytest.mark.django_db
def test_setup_roles_assigns_admin_every_known_perm() -> None:
    """El grupo Administrador tiene los permisos de Django que existen."""
    call_command("setup_roles", verbosity=0)
    group = Group.objects.get(name=str(Role.ADMIN))
    assigned = set(
        group.permissions.values_list("content_type__app_label", "codename")
    )
    existing = set(
        Permission.objects.values_list("content_type__app_label", "codename")
    )
    declared = set()
    for app, codenames in PERMISSIONS_BY_APP.items():
        for codename in codenames:
            declared.add((app, codename))
    expected = declared & existing
    assert expected.issubset(assigned)


@pytest.mark.django_db
def test_setup_roles_is_idempotent() -> None:
    """Ejecutar ``setup_roles`` dos veces no duplica grupos."""
    call_command("setup_roles", verbosity=0)
    call_command("setup_roles", verbosity=0)
    assert Group.objects.count() == len(Role)


@pytest.mark.django_db
def test_setup_roles_keeps_admin_perm_view_user() -> None:
    """El admin conserva permiso de ver usuarios tras correr dos veces."""
    call_command("setup_roles", verbosity=0)
    group = Group.objects.get(name=str(Role.ADMIN))
    has_view = group.permissions.filter(codename="view_user").exists()
    assert has_view


@pytest.mark.django_db
def test_setup_roles_removes_lost_permissions() -> None:
    """Si un rol pierde un permiso existente, ``setup_roles`` lo retira."""
    call_command("setup_roles", verbosity=0)
    group = Group.objects.get(name=str(Role.VIEWER))
    view_user = Permission.objects.get(codename="view_user")
    group.permissions.add(view_user)
    call_command("setup_roles", verbosity=0)
    group.refresh_from_db()
    assert view_user not in group.permissions.all()


@pytest.mark.django_db
def test_setup_roles_resolves_every_permission() -> None:
    """Todos los permisos de cada rol existen en la BD (sin faltantes)."""
    call_command("setup_roles", verbosity=0)
    for role, perms in ROLE_PERMISSIONS.items():
        group = Group.objects.get(name=str(role))
        assigned = {
            f"{app}.{code}"
            for app, code in group.permissions.values_list(
                "content_type__app_label", "codename"
            )
        }
        assert assigned == set(perms), role
