"""Tests de servicios de socios."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.db import IntegrityError

from apps.partners import services
from apps.partners.selectors import active_suppliers


@pytest.mark.django_db
def test_create_supplier_persists() -> None:
    """Crea proveedor."""
    supplier = services.create_supplier(
        name="Proveedor A", tax_id="A-1",
    )
    assert supplier.pk is not None
    assert supplier.is_active is True


@pytest.mark.django_db
def test_create_customer_persists_with_credit_limit() -> None:
    """Crea cliente con limite de credito."""
    customer = services.create_customer(
        name="Cliente B", tax_id="B-1",
        credit_limit=Decimal("5000"),
    )
    assert customer.credit_limit == Decimal("5000.0000")


@pytest.mark.django_db
def test_update_supplier_changes_fields() -> None:
    """Update cambia campos."""
    supplier = services.create_supplier(name="S1", tax_id="S1")
    services.update_supplier(supplier, lead_time_days=15)
    supplier.refresh_from_db()
    assert supplier.lead_time_days == 15


@pytest.mark.django_db
def test_supplier_tax_id_is_unique() -> None:
    """Tax_id es unico."""
    services.create_supplier(name="X", tax_id="UNIQ-1")
    with pytest.raises(IntegrityError):
        services.create_supplier(name="Y", tax_id="UNIQ-1")


@pytest.mark.django_db
def test_selectors_return_only_active() -> None:
    """Los selectores filtran por is_active."""
    services.create_supplier(name="A1", tax_id="A-1")
    s2 = services.create_supplier(name="A2", tax_id="A-2")
    s2.is_active = False
    s2.save()
    actives = list(active_suppliers())
    assert len(actives) == 1
    assert actives[0].name == "A1"
