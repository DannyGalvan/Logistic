"""Tests de los receivers de auditoria (modelos y sesiones)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.audit.models import AuditLog
from apps.audit.registry import get_excluded, is_audited
from apps.catalog.services import update_product

pytestmark = pytest.mark.django_db


def test_registry_is_case_insensitive() -> None:
    """``catalog.Product`` y ``catalog.product`` son el mismo modelo."""
    assert is_audited("catalog.product")
    assert is_audited("catalog.Product")
    assert "updated_at" in get_excluded("CATALOG.PRODUCT")


def test_create_update_delete_are_logged(product_factory) -> None:
    """Crear, editar y borrar un modelo auditado deja rastro con diff."""
    product = product_factory(name="Antes")
    assert AuditLog.objects.filter(action="CREATE", object_id=str(product.pk)).exists()

    update_product(product, name="Despues")
    update = AuditLog.objects.get(action="UPDATE", object_id=str(product.pk))
    assert update.changes["name"] == ["Antes", "Despues"]
    assert "updated_at" not in update.changes

    product_id = product.pk
    product.delete()
    assert AuditLog.objects.filter(action="DELETE", object_id=str(product_id)).exists()


def test_save_without_changes_is_not_logged(product_factory) -> None:
    """Un ``save`` sin cambios no genera ``UPDATE``."""
    product = product_factory()
    product.save()
    assert not AuditLog.objects.filter(action="UPDATE").exists()


def test_unaudited_model_is_ignored(warehouse_with_locations) -> None:
    """Las ubicaciones no estan registradas: no generan bitacora."""
    location = warehouse_with_locations.locations.first()
    location.name = "Otro"
    location.save()
    assert not AuditLog.objects.filter(object_repr__icontains="Otro").exists()


def test_login_logout_and_failed_login(client, django_user_model) -> None:
    """Inicio, cierre e intento fallido de sesion quedan registrados."""
    django_user_model.objects.create_user(username="ana", password="Segura-123")
    client.post(reverse("accounts:login"), {"username": "ana", "password": "mala"})
    failed = AuditLog.objects.get(action="LOGIN_FAILED")
    assert failed.object_repr == "ana"
    assert failed.ip_address == "127.0.0.1"

    client.post(reverse("accounts:login"), {"username": "ana", "password": "Segura-123"})
    assert AuditLog.objects.filter(action="LOGIN", user__username="ana").exists()
    client.post(reverse("accounts:logout"))
    assert AuditLog.objects.filter(action="LOGOUT", user__username="ana").exists()
