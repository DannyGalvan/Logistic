"""Serializers de ``partners``."""

from __future__ import annotations

from rest_framework import serializers

from ..models import Customer, Supplier

PARTNER_FIELDS = [
    "id", "name", "tax_id", "email", "phone", "address", "contact_name", "notes",
    "is_active",
]


class SupplierSerializer(serializers.ModelSerializer):
    """Proveedor."""

    class Meta:
        model = Supplier
        fields = [*PARTNER_FIELDS, "lead_time_days", "payment_terms"]
        read_only_fields = ["is_active"]


class CustomerSerializer(serializers.ModelSerializer):
    """Cliente."""

    class Meta:
        model = Customer
        fields = [*PARTNER_FIELDS, "credit_limit"]
        read_only_fields = ["is_active"]
