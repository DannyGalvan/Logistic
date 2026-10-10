"""Tests de servicios de audit."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

from apps.audit.services import log


@pytest.fixture
def user(db):
    """Crea usuario de prueba."""
    return get_user_model().objects.create_user(
        username="audit", password="x1234567"
    )


@pytest.mark.django_db
def test_log_create_creates_entry(user) -> None:
    """``log`` crea un registro en bitacora."""
    entry = log(user=user, action="LOGIN", obj=user, ip_address="127.0.0.1")
    assert entry.user == user
    assert entry.action == "LOGIN"


@pytest.mark.django_db
def test_log_anonymous_user() -> None:
    """``log`` acepta usuario anonimo (None)."""
    entry = log(user=None, action="LOGIN_FAILED")
    assert entry.user is None


@pytest.mark.django_db
def test_log_with_changes_payload(user) -> None:
    """``log`` guarda los cambios como JSONField."""
    entry = log(
        user=user,
        action="UPDATE",
        obj=user,
        changes={"email": ["old@example.com", "new@example.com"]},
    )
    assert entry.changes == {
        "email": ["old@example.com", "new@example.com"],
    }
