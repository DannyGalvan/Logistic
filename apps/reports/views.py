"""Vistas web y API del modulo de reportes."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView

from apps.core.views import LoginRequiredMixin, PermissionRequiredMixin

from .datasets import TabularData
from .exporters import get_exporter
from .selectors import (
    dashboard_kpis,
    inventory_valuation,
    movements_by_day,
    top_moving_products,
)


class DashboardView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Dashboard principal con KPIs y graficos."""

    permission_required = "reports.view_reports"
    template_name = "reports/dashboard.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Renderiza el dashboard."""
        context: dict[str, Any] = {
            "kpis": dashboard_kpis(),
            "top_products": list(top_moving_products()),
            "movements_by_day": list(movements_by_day()),
        }
        return render(request, self.template_name, context)


class InventoryValuationView(
    LoginRequiredMixin, PermissionRequiredMixin, View,
):
    """Vista del reporte de valoracion de inventario."""

    permission_required = "reports.view_reports"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Devuelve CSV / XLSX / PDF segun ``?export=``."""
        total = inventory_valuation()
        data = TabularData(
            title="Valoracion de inventario",
            headers=["Metrica", "Valor"],
            rows=[["Total", str(total)]],
            filename="valoracion_inventario",
        )
        fmt = request.GET.get("export", "csv")
        return get_exporter(fmt).to_response(data)


class ChartDataView(APIView):
    """Endpoint API JSON para graficos Chart.js."""

    def get(self, request: HttpRequest) -> JsonResponse:
        """Devuelve series para el grafico ``movements_by_day``."""
        return JsonResponse({
            "series": [
                {
                    "name": "Movimientos",
                    "data": list(movements_by_day().values("day", "count")),
                }
            ]
        })


__all__ = [
    "DashboardView",
    "InventoryValuationView",
    "ChartDataView",
]
