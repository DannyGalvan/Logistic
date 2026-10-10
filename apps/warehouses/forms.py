"""Formularios de la app ``warehouses``."""

from __future__ import annotations

from django import forms

from .models import Location, Warehouse


class WarehouseForm(forms.ModelForm):
    """Formulario de alta/edicion de almacenes."""

    class Meta:
        model = Warehouse
        fields = ["code", "name", "address", "manager", "is_active"]


class LocationForm(forms.ModelForm):
    """Formulario de alta/edicion de ubicaciones."""

    class Meta:
        model = Location
        fields = ["code", "name", "location_type", "is_active"]


__all__ = ["WarehouseForm", "LocationForm"]
