"""ViewSets de ``quality``."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.api.viewsets import BaseReadOnlyViewSet

from .. import services
from ..models import LintRun
from . import serializers


class LintRunViewSet(BaseReadOnlyViewSet):
    """Corridas de Pylint (lectura) y ejecucion bajo demanda."""

    queryset = LintRun.objects.order_by("-created_at")
    serializer_class = serializers.LintRunSerializer
    filterset_fields = ["status", "source"]
    action_permissions = {"run": ["accounts.run_lint"]}

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        """El detalle incluye los mensajes."""
        if self.action == "retrieve":
            return serializers.LintRunDetailSerializer
        return super().get_serializer_class()

    @extend_schema(request=serializers.RunInputSerializer,
                   responses=serializers.LintRunSerializer)
    @action(detail=False, methods=["post"])
    def run(self, request):
        """Ejecuta Pylint y guarda la corrida."""
        payload = serializers.RunInputSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        run = services.LintService().run_project(
            targets=payload.validated_data.get("targets") or None,
            user=request.user,
            source=LintRun.Source.WEB,
        )
        return Response(
            serializers.LintRunSerializer(run).data, status=status.HTTP_201_CREATED
        )
