"""ViewSets de ``purchasing``."""

from __future__ import annotations

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.api.viewsets import BaseReadOnlyViewSet

from .. import services
from ..models import PurchaseOrder
from . import serializers


class PurchaseOrderViewSet(mixins.CreateModelMixin, BaseReadOnlyViewSet):
    """Ordenes de compra: alta, lineas, confirmacion, recepcion, cancelacion."""

    queryset = PurchaseOrder.objects.prefetch_related("lines").order_by("-code")
    serializer_class = serializers.PurchaseOrderSerializer
    filterset_fields = ["status", "supplier", "warehouse"]
    search_fields = ["code", "supplier__name"]
    action_permissions = {
        "add_line": ["purchasing.change_purchaseorder"],
        "confirm": ["accounts.confirm_purchaseorder"],
        "cancel": ["purchasing.change_purchaseorder"],
        "receive": ["accounts.receive_purchaseorder"],
    }

    @transaction.atomic
    def perform_create(self, serializer) -> None:  # type: ignore[no-untyped-def]
        """Crea la OC en borrador y sus lineas iniciales via service."""
        data = dict(serializer.validated_data)
        lines = data.pop("lines", [])
        service = services.PurchaseService()
        order = service.create_order(user=self.request.user, **data)
        for line in lines:
            service.add_line(order, **line)
        serializer.instance = order

    def _respond(self, order: PurchaseOrder, code: int = status.HTTP_200_OK) -> Response:
        """Devuelve la orden actualizada."""
        order.refresh_from_db()
        return Response(self.get_serializer(order).data, status=code)

    @extend_schema(request=serializers.PurchaseAddLineSerializer)
    @action(detail=True, methods=["post"], url_path="lines")
    def add_line(self, request, pk=None):  # pylint: disable=unused-argument
        """Agrega una linea (solo en borrador)."""
        order = self.get_object()
        payload = serializers.PurchaseAddLineSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        services.PurchaseService().add_line(order, **payload.validated_data)
        return self._respond(order, status.HTTP_201_CREATED)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):  # pylint: disable=unused-argument
        """Confirma la orden."""
        order = self.get_object()
        services.PurchaseService().confirm(order)
        return self._respond(order)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):  # pylint: disable=unused-argument
        """Cancela la orden."""
        order = self.get_object()
        services.PurchaseService().cancel(order)
        return self._respond(order)

    @extend_schema(request=serializers.PurchaseReceiveInputSerializer,
                   responses=serializers.GoodsReceiptSerializer)
    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):  # pylint: disable=unused-argument
        """Registra una recepcion parcial o total."""
        order = self.get_object()
        payload = serializers.PurchaseReceiveInputSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        receipt = services.PurchaseService().receive(
            order,
            location=payload.validated_data["location"],
            lines=[
                services.ReceiptLineInput(**line)
                for line in payload.validated_data["lines"]
            ],
            user=request.user,
        )
        return Response(
            serializers.GoodsReceiptSerializer(receipt).data,
            status=status.HTTP_201_CREATED,
        )
