"""Serializers de ``warehouses``."""

from __future__ import annotations

from rest_framework import serializers

from ..models import Location, Warehouse


class LocationSerializer(serializers.ModelSerializer):
    """Ubicacion dentro de un almacen."""

    class Meta:
        model = Location
        fields = ["id", "warehouse", "code", "name", "location_type", "is_active"]
        read_only_fields = ["is_active"]


class WarehouseSerializer(serializers.ModelSerializer):
    """Almacen; al crearlo se generan sus ubicaciones por defecto."""

    locations = LocationSerializer(many=True, read_only=True)

    class Meta:
        model = Warehouse
        fields = ["id", "code", "name", "address", "manager", "is_active", "locations"]
        read_only_fields = ["is_active"]
