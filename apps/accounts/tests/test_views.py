"""Tests de las vistas de ``accounts``."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.roles import Role


@pytest.fixture
def admin_user_test():
    """Crea un superusuario activo (no choca con la fixture pytest-django)."""
    user_model = get_user_model()
    return user_model.objects.create_superuser(
        username="admin_test",
        email="admin@example.com",
        password="adminpass123",
    )


@pytest.mark.django_db
def test_login_renders_login_template(client) -> None:
    """GET /cuentas/login/ muestra el formulario."""
    response = client.get(reverse("accounts:login"))
    assert response.status_code == 200
    assert b"Iniciar sesion" in response.content


@pytest.mark.django_db
def test_login_with_valid_credentials_redirects(client) -> None:
    """POST con credenciales validas redirige al dashboard."""
    user_model = get_user_model()
    user_model.objects.create_user(
        username="alice",
        password="Secreta123!",
        email="alice@example.com",
    )
    response = client.post(
        reverse("accounts:login"),
        data={"username": "alice", "password": "Secreta123!"},
    )
    assert response.status_code == 302
    assert reverse("core:dashboard") in response.url


@pytest.mark.django_db
def test_login_with_invalid_password_shows_error(client) -> None:
    """POST con password incorrecto re-renderiza con error."""
    user_model = get_user_model()
    user_model.objects.create_user(
        username="bob", password="Secreta123!", email="bob@example.com"
    )
    response = client.post(
        reverse("accounts:login"),
        data={"username": "bob", "password": "OtraCosa"},
    )
    assert response.status_code == 200
    assert b"Iniciar sesion" in response.content


@pytest.mark.django_db
def test_profile_redirects_anonymous_users(client) -> None:
    """Acceder al perfil sin login redirige a login."""
    response = client.get(reverse("accounts:profile"))
    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_profile_renders_for_authenticated_user(client_logged) -> None:
    """El usuario autenticado ve su perfil."""
    response = client_logged.get(reverse("accounts:profile"))
    assert response.status_code == 200
    assert b"Mi perfil" in response.content


@pytest.mark.django_db
def test_user_list_requires_login(client) -> None:
    """El listado de usuarios requiere autenticacion."""
    response = client.get(reverse("accounts:user-list"))
    assert response.status_code in (302, 403)


@pytest.mark.django_db
def test_user_list_renders_for_admin(client_logged, admin_user_test) -> None:
    """El admin ve el listado de usuarios."""
    client_logged.force_login(admin_user_test)
    response = client_logged.get(reverse("accounts:user-list"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_user_create_view_creates_user(client_logged, admin_user_test) -> None:
    """El admin puede crear un usuario nuevo."""
    client_logged.force_login(admin_user_test)
    response = client_logged.post(
        reverse("accounts:user-create"),
        data={
            "username": "newby",
            "password1": "NuevaClave123!",
            "password2": "NuevaClave123!",
            "email": "newby@example.com",
        },
    )
    assert response.status_code == 302
    user_model = get_user_model()
    assert user_model.objects.filter(username="newby").exists()


@pytest.mark.django_db
def test_user_create_password_mismatch_returns_form(client_logged, admin_user_test) -> None:
    """Passwords que difieren re-renderizan el formulario."""
    client_logged.force_login(admin_user_test)
    response = client_logged.post(
        reverse("accounts:user-create"),
        data={
            "username": "newby2",
            "password1": "ClaveA123!",
            "password2": "ClaveB123!",
        },
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_logout_redirects_to_login(admin_user_test, client) -> None:
    """El logout redirige al login."""
    client.force_login(admin_user_test)
    response = client.post(reverse("accounts:logout"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_login_redirects_authenticated_user(client_logged, admin_user_test) -> None:
    """Un usuario autenticado que va a login es redirigido al dashboard."""
    client_logged.force_login(admin_user_test)
    response = client_logged.get(reverse("accounts:login"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_user_list_denied_for_supervisor(client_as, users_by_role) -> None:
    """El supervisor NO tiene permiso para gestionar usuarios (segun plan)."""
    client = client_as(Role.SUPERVISOR)
    response = client.get(reverse("accounts:user-list"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_user_list_denied_for_viewer(client_as, users_by_role) -> None:
    """El usuario de consulta NO debe ver el listado de usuarios."""
    client = client_as(Role.VIEWER)
    response = client.get(reverse("accounts:user-list"))
    assert response.status_code == 403
