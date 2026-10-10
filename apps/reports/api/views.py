"""Endpoints API de ``reports``."""

from __future__ import annotations

from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.permissions import RequiredPermissions

from ..selectors import dashboard_kpis


class KpiView(APIView):
    """KPIs del dashboard."""

    permission_classes = [RequiredPermissions]
    required_permissions = ["reports.view_reports"]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):  # pylint: disable=unused-argument
        """Devuelve los indicadores agregados."""
        kpis = dashboard_kpis()
        kpis["stock_value"] = str(kpis["stock_value"])
        return Response(kpis)
