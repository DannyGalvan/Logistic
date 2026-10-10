"""ViewSets de ``inventory``."""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.api.viewsets import BaseReadOnlyViewSet

from .. import selectors, services
from ..models import CycleCount, Lot, Stock, StockMovement
from . import serializers

MOVE_PERMISSION = ["inventory.add_stockmovement"]
COUNT_PERMISSION = ["inventory.add_cyclecount"]


class LotViewSet(BaseReadOnlyViewSet):
    """Lotes (solo lectura)."""

    queryset = Lot.objects.order_by("expires_at", "lot_number")
    serializer_class = serializers.LotSerializer
    search_fields = ["lot_number", "product__sku"]
    filterset_fields = ["product"]


class StockViewSet(BaseReadOnlyViewSet):
    """Existencias (solo lectura)."""

    queryset = Stock.objects.filter(quantity__gt=0).order_by("product__sku")
    serializer_class = serializers.StockSerializer
    filterset_fields = ["product", "location", "location__warehouse", "lot"]


class StockMovementViewSet(BaseReadOnlyViewSet):
    """Movimientos (solo lectura) y acciones para registrarlos."""

    queryset = StockMovement.objects.order_by("-created_at")
    serializer_class = serializers.StockMovementSerializer
    filterset_fields = ["product", "movement_type", "lot"]
    search_fields = ["reference", "product__sku"]
    action_permissions = {
        "receive": MOVE_PERMISSION,
        "issue": MOVE_PERMISSION,
        "transfer": MOVE_PERMISSION,
        "adjust": MOVE_PERMISSION,
        "kardex": ["accounts.view_kardex"],
    }

    def _run(self, input_class, method: str) -> Response:
        """Valida la entrada, llama al service y devuelve el movimiento."""
        data = input_class(data=self.request.data)
        data.is_valid(raise_exception=True)
        movement = getattr(services.InventoryService(), method)(
            user=self.request.user, **data.validated_data
        )
        output = serializers.StockMovementSerializer(movement)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @extend_schema(request=serializers.ReceiveInputSerializer,
                   responses=serializers.StockMovementSerializer)
    @action(detail=False, methods=["post"])
    def receive(self, request):  # pylint: disable=unused-argument
        """Registra una entrada."""
        return self._run(serializers.ReceiveInputSerializer, "receive")

    @extend_schema(request=serializers.IssueInputSerializer,
                   responses=serializers.StockMovementSerializer)
    @action(detail=False, methods=["post"])
    def issue(self, request):  # pylint: disable=unused-argument
        """Registra una salida."""
        return self._run(serializers.IssueInputSerializer, "issue")

    @extend_schema(request=serializers.TransferInputSerializer,
                   responses=serializers.StockMovementSerializer)
    @action(detail=False, methods=["post"])
    def transfer(self, request):  # pylint: disable=unused-argument
        """Registra una transferencia."""
        return self._run(serializers.TransferInputSerializer, "transfer")

    @extend_schema(request=serializers.AdjustInputSerializer,
                   responses=serializers.StockMovementSerializer)
    @action(detail=False, methods=["post"])
    def adjust(self, request):  # pylint: disable=unused-argument
        """Ajusta la existencia a la cantidad contada."""
        return self._run(serializers.AdjustInputSerializer, "adjust")

    @extend_schema(parameters=[serializers.KardexQuerySerializer],
                   responses=serializers.KardexRowSerializer(many=True))
    @action(detail=False, methods=["get"])
    def kardex(self, request):
        """Kardex valorizado de un producto."""
        query = serializers.KardexQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        rows = selectors.kardex(**query.validated_data)
        return Response(serializers.KardexRowSerializer(rows, many=True).data)


class CycleCountViewSet(mixins.CreateModelMixin, BaseReadOnlyViewSet):
    """Conteos ciclicos y su ciclo de vida."""

    queryset = CycleCount.objects.prefetch_related("lines").order_by("-code")
    serializer_class = serializers.CycleCountSerializer
    filterset_fields = ["status", "warehouse"]
    action_permissions = {
        "start": COUNT_PERMISSION,
        "record": COUNT_PERMISSION,
        "cancel": COUNT_PERMISSION,
        "approve": ["accounts.approve_cyclecount"],
    }

    def perform_create(self, serializer) -> None:  # type: ignore[no-untyped-def]
        """Crea el conteo (snapshot del stock) via service."""
        serializer.instance = services.CycleCountService().create(
            user=self.request.user, **serializer.validated_data
        )

    def _respond(self, cycle: CycleCount) -> Response:
        """Devuelve el conteo actualizado."""
        cycle.refresh_from_db()
        return Response(self.get_serializer(cycle).data)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):  # pylint: disable=unused-argument
        """Pasa el conteo a ``IN_PROGRESS``."""
        cycle = self.get_object()
        services.CycleCountService().start(cycle)
        return self._respond(cycle)

    @extend_schema(request=serializers.CycleCountRecordSerializer)
    @action(detail=True, methods=["post"])
    def record(self, request, pk=None):  # pylint: disable=unused-argument
        """Registra cantidades contadas por linea."""
        cycle = self.get_object()
        payload = serializers.CycleCountRecordSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        service = services.CycleCountService()
        for item in payload.validated_data["lines"]:
            line = get_object_or_404(cycle.lines, pk=item["id"])
            service.record(line, item["counted_quantity"])
        return self._respond(cycle)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):  # pylint: disable=unused-argument
        """Aprueba el conteo y genera ajustes."""
        cycle = self.get_object()
        services.CycleCountService().approve(cycle, user=request.user)
        return self._respond(cycle)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):  # pylint: disable=unused-argument
        """Cancela el conteo."""
        cycle = self.get_object()
        services.CycleCountService().cancel(cycle)
        return self._respond(cycle)
