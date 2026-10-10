"""Tests de vistas del modulo quality."""

from __future__ import annotations

import pytest
from django.urls import reverse



@pytest.mark.django_db
def test_quality_dashboard_renders(admin_client) -> None:
    """El dashboard de calidad carga."""
    response = admin_client.get(reverse("quality:dashboard"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_quality_run_list_renders(admin_client) -> None:
    """La lista de corridas carga."""
    response = admin_client.get(reverse("quality:run-list"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_quality_catalog_renders(admin_client) -> None:
    """El catalogo carga."""
    response = admin_client.get(reverse("quality:catalog"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_quality_snippet_renders(admin_client) -> None:
    """El formulario de snippet carga."""
    response = admin_client.get(reverse("quality:snippet"))
    assert response.status_code == 200
