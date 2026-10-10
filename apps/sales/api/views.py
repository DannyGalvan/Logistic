"""ViewSets de ``sales``."""

from __future__ import annotations

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.api.viewsets import BaseReadOnlyViewSet

from .. import services
from ..models import SalesOrder
from . import serializers


class SalesOrderViewSet(mixins.CreateModelMixin, BaseReadOnlyViewSet):
    """Ordenes de venta: alta, lineas, confirmacion, picking y despacho."""

    queryset = SalesOrder.objects.prefetch_related("lines").order_by("-code")
    serializer_class = serializers.SalesOrderSerializer
    filterset_fields = ["status", "customer", "warehouse"]
    search_fields = ["code", "customer__name"]
    action_permissions = {
        "add_line": ["sales.change_salesorder"],
        "confirm": ["accounts.confirm_salesorder"],
        "cancel": ["sales.change_salesorder"],
        "suggest_picking": ["sales.view_salesorder"],
        "ship": ["accounts.ship_salesorder"],
    }

    @transaction.atomic
    def perform_create(self, serializer) -> None:  # type: ignore[no-untyped-def]
        """Crea la OV en borrador y sus lineas iniciales via service."""
        data = dict(serializer.validated_data)
        lines = data.pop("lines", [])
        service = services.SalesService()
        order = service.create_order(user=self.request.user, **data)
        for line in lines:
            service.add_line(order, **line)
        serializer.instance = order

    def _respond(self, order: SalesOrder, code: int = status.HTTP_200_OK) -> Response:
        """Devuelve la orden actualizada."""
        order.refresh_from_db()
        return Response(self.get_serializer(order).data, status=code)

    @extend_schema(request=serializers.SalesAddLineSerializer)
    @action(detail=True, methods=["post"], url_path="lines")
    def add_line(self, request, pk=None):  # pylint: disable=unused-argument
        """Agrega una linea (solo en borrador)."""
        order = self.get_object()
        payload = serializers.SalesAddLineSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        services.SalesService().add_line(order, **payload.validated_data)
        return self._respond(order, status.HTTP_201_CREATED)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):  # pylint: disable=unused-argument
        """Confirma la orden."""
        order = self.get_object()
        services.SalesService().confirm(order)
        return self._respond(order)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):  # pylint: disable=unused-argument
        """Cancela la orden."""
        order = self.get_object()
        services.SalesService().cancel(order)
        return self._respond(order)

    @extend_schema(responses=serializers.PickingSuggestionSerializer(many=True))
    @action(detail=True, methods=["get"], url_path="suggest-picking")
    def suggest_picking(self, request, pk=None):  # pylint: disable=unused-argument
        """Sugiere ubicaciones/lotes segun la estrategia de rotacion."""
        suggestions = services.SalesService().suggest_picking(self.get_object())
        return Response(
            serializers.PickingSuggestionSerializer(suggestions, many=True).data
        )

    @extend_schema(request=serializers.ShipInputSerializer,
                   responses=serializers.ShipmentSerializer)
    @action(detail=True, methods=["post"])
    def ship(self, request, pk=None):  # pylint: disable=unused-argument
        """Registra un despacho parcial o total."""
        order = self.get_object()
        payload = serializers.ShipInputSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        shipment = services.SalesService().ship(
            order,
            lines=[services.ShipLineInput(**line) for line in data["lines"]],
            user=request.user,
            carrier=data["carrier"],
            tracking_number=data["tracking_number"],
        )
        return Response(
            serializers.ShipmentSerializer(shipment).data,
            status=status.HTTP_201_CREATED,
        )
