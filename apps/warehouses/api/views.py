"""ViewSets de ``warehouses``."""

from __future__ import annotations

from apps.core.api.viewsets import ServiceModelViewSet

from .. import services
from ..models import Location, Warehouse
from . import serializers


class WarehouseViewSet(ServiceModelViewSet):
    """Almacenes."""

    queryset = Warehouse.objects.prefetch_related("locations").order_by("code")
    serializer_class = serializers.WarehouseSerializer
    create_service = services.create_warehouse
    update_service = services.update_warehouse
    search_fields = ["code", "name"]
    filterset_fields = ["is_active"]


class LocationViewSet(ServiceModelViewSet):
    """Ubicaciones."""

    queryset = Location.objects.select_related("warehouse").order_by("warehouse__code", "code")
    serializer_class = serializers.LocationSerializer
    create_service = services.create_location
    update_service = services.update_location
    service_accepts_user = False
    search_fields = ["code", "name"]
    filterset_fields = ["warehouse", "location_type", "is_active"]
