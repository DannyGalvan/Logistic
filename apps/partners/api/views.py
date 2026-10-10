"""ViewSets de ``partners``."""

from __future__ import annotations

from apps.core.api.viewsets import ServiceModelViewSet

from .. import services
from ..models import Customer, Supplier
from . import serializers


class SupplierViewSet(ServiceModelViewSet):
    """Proveedores."""

    queryset = Supplier.objects.order_by("name")
    serializer_class = serializers.SupplierSerializer
    create_service = services.create_supplier
    update_service = services.update_supplier
    search_fields = ["name", "tax_id", "email"]
    filterset_fields = ["is_active"]


class CustomerViewSet(ServiceModelViewSet):
    """Clientes."""

    queryset = Customer.objects.order_by("name")
    serializer_class = serializers.CustomerSerializer
    create_service = services.create_customer
    update_service = services.update_customer
    search_fields = ["name", "tax_id", "email"]
    filterset_fields = ["is_active"]
