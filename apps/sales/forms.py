"""Formularios de ``sales``."""

from __future__ import annotations

from django import forms

from apps.catalog.models import Product

from .models import SalesOrder


class SalesOrderForm(forms.ModelForm):
    """Formulario de alta de orden."""

    class Meta:
        model = SalesOrder
        fields = ["customer", "warehouse", "order_date", "notes"]
        widgets = {
            "order_date": forms.DateInput(attrs={"type": "date"}),
        }


class SalesOrderLineForm(forms.Form):
    """Formulario para agregar una linea."""

    product = forms.ModelChoiceField(queryset=Product.active.all())
    quantity = forms.DecimalField(max_digits=14, decimal_places=3)
    unit_price = forms.DecimalField(max_digits=14, decimal_places=4)


__all__ = ["SalesOrderForm", "SalesOrderLineForm"]
