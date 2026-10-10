"""Pruebas del comando ``seed_demo``."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from apps.catalog.models import Product
from apps.inventory.models import Alert, CycleCount, StockMovement
from apps.purchasing.models import PurchaseOrder
from apps.sales.models import SalesOrder

pytestmark = pytest.mark.django_db


def _counts() -> dict[str, int]:
    """Totales por modelo para comparar corridas."""
    return {
        "users": get_user_model().objects.count(),
        "products": Product.objects.count(),
        "movements": StockMovement.objects.count(),
        "purchase_orders": PurchaseOrder.objects.count(),
        "sales_orders": SalesOrder.objects.count(),
        "cycle_counts": CycleCount.objects.count(),
    }


@override_settings(DEBUG=True)
def test_seed_demo_is_idempotent() -> None:
    """Dos corridas seguidas no duplican datos."""
    call_command("seed_demo", verbosity=0)
    first = _counts()
    call_command("seed_demo", verbosity=0)
    assert _counts() == first
    assert first["products"] == 30
    assert first["purchase_orders"] == 3
    assert first["sales_orders"] == 3


@override_settings(DEBUG=True)
def test_seed_demo_creates_expected_states() -> None:
    """OC/OV quedan en los estados del plan y hay alertas activas."""
    call_command("seed_demo", verbosity=0)
    assert set(PurchaseOrder.objects.values_list("status", flat=True)) == {
        "RECEIVED", "PARTIALLY_RECEIVED", "DRAFT",
    }
    assert set(SalesOrder.objects.values_list("status", flat=True)) == {
        "SHIPPED", "CONFIRMED", "DRAFT",
    }
    assert CycleCount.objects.filter(status="IN_PROGRESS").exists()
    assert StockMovement.objects.filter(movement_type="TRANSFER").count() == 2
    assert Alert.objects.filter(alert_type="LOW_STOCK").exists()
    assert Alert.objects.exclude(alert_type="LOW_STOCK").exists()


@override_settings(DEBUG=True)
def test_seed_demo_users_have_role_permissions() -> None:
    """Los usuarios demo heredan los permisos de su grupo."""
    call_command("seed_demo", verbosity=0)
    users = get_user_model().objects
    assert users.get(username="almacenista").has_perm("accounts.receive_purchaseorder")
    assert users.get(username="supervisor").has_perm("accounts.approve_cyclecount")
    assert not users.get(username="consulta").has_perm("purchasing.add_purchaseorder")


@override_settings(DEBUG=False)
def test_seed_demo_refuses_without_debug() -> None:
    """Con ``DEBUG=False`` exige ``--force``."""
    with pytest.raises(CommandError):
        call_command("seed_demo", verbosity=0)
