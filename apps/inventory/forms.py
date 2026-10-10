"""Formularios de ``inventory``."""

from __future__ import annotations

from decimal import Decimal

from django import forms

from apps.catalog.models import Product
from apps.warehouses.models import Location, Warehouse

from .models import CycleCount, Lot


class _BaseMovementForm(forms.Form):
    """Campos comunes a entrada / salida / ajuste."""

    product = forms.ModelChoiceField(queryset=Product.active.all())
    location = forms.ModelChoiceField(
        queryset=Location.objects.filter(is_active=True)
    )
    quantity = forms.DecimalField(max_digits=14, decimal_places=3)
    reference = forms.CharField(max_length=80, required=False)


class ReceiveForm(_BaseMovementForm):
    """Formulario de recepcion."""

    warehouse = forms.ModelChoiceField(queryset=Warehouse.active.all())
    unit_cost = forms.DecimalField(max_digits=14, decimal_places=4)
    lot_number = forms.CharField(max_length=40, required=False)
    expires_at = forms.DateField(required=False)
    manufactured_at = forms.DateField(required=False)

    def __init__(self, *args, **kwargs):
        """Inicializa restringiendo location al warehouse seleccionado."""
        super().__init__(*args, **kwargs)
        warehouse_id = self.data.get(self.add_prefix("warehouse")) or None
        if warehouse_id:
            self.fields["location"].queryset = Location.objects.filter(
                is_active=True, warehouse_id=warehouse_id
            )

    def clean_quantity(self) -> Decimal:
        """Cantidad > 0."""
        qty = self.cleaned_data["quantity"]
        if qty <= 0:
            raise forms.ValidationError("Cantidad debe ser mayor a cero.")
        return qty


class _LotMixin(forms.Form):
    """Lote opcional para productos con ``track_lots``."""

    lot = forms.ModelChoiceField(
        queryset=Lot.objects.order_by("expires_at", "lot_number"),
        required=False,
        label="Lote",
        help_text="Obligatorio solo si el producto maneja lotes.",
    )


class IssueForm(_LotMixin, _BaseMovementForm):
    """Formulario de salida."""


class TransferForm(_LotMixin, _BaseMovementForm):
    """Formulario de transferencia."""

    to_location = forms.ModelChoiceField(
        queryset=Location.objects.filter(is_active=True)
    )

    def clean(self):
        """Origen y destino deben diferir."""
        cleaned = super().clean()
        origin = cleaned.get("location")
        dest = cleaned.get("to_location")
        if origin and dest and origin.pk == dest.pk:
            self.add_error("to_location", "Debe diferir del origen.")
        return cleaned


class AdjustForm(_LotMixin, _BaseMovementForm):
    """Formulario de ajuste por conteo."""

    quantity = None
    counted_quantity = forms.DecimalField(max_digits=14, decimal_places=3)


class CycleCountForm(forms.ModelForm):
    """Formulario de alta de conteo ciclico."""

    class Meta:
        model = CycleCount
        fields = ["warehouse", "location", "notes"]


__all__ = [
    "ReceiveForm",
    "IssueForm",
    "TransferForm",
    "AdjustForm",
    "CycleCountForm",
]
