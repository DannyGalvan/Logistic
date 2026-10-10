"""Formularios de ``purchasing``."""

from __future__ import annotations

from django import forms

from apps.catalog.models import Product

from .models import PurchaseOrder


class PurchaseOrderForm(forms.ModelForm):
    """Formulario de alta de orden."""

    class Meta:
        model = PurchaseOrder
        fields = [
            "supplier",
            "warehouse",
            "order_date",
            "expected_date",
            "notes",
        ]
        widgets = {
            "order_date": forms.DateInput(attrs={"type": "date"}),
            "expected_date": forms.DateInput(attrs={"type": "date"}),
        }


class PurchaseOrderLineForm(forms.Form):
    """Formulario para agregar una linea a la orden."""

    product = forms.ModelChoiceField(queryset=Product.active.all())
    quantity = forms.DecimalField(max_digits=14, decimal_places=3)
    unit_cost = forms.DecimalField(max_digits=14, decimal_places=4)


__all__ = ["PurchaseOrderForm", "PurchaseOrderLineForm"]
