"""Formularios de la app ``partners``."""

from __future__ import annotations

from django import forms

from .models import Customer, Supplier


class SupplierForm(forms.ModelForm):
    """Formulario de proveedores."""

    class Meta:
        model = Supplier
        fields = [
            "name",
            "tax_id",
            "email",
            "phone",
            "address",
            "contact_name",
            "notes",
            "lead_time_days",
            "payment_terms",
            "is_active",
        ]


class CustomerForm(forms.ModelForm):
    """Formulario de clientes."""

    class Meta:
        model = Customer
        fields = [
            "name",
            "tax_id",
            "email",
            "phone",
            "address",
            "contact_name",
            "notes",
            "credit_limit",
            "is_active",
        ]


__all__ = ["SupplierForm", "CustomerForm"]
