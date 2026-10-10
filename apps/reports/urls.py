"""URLs de ``reports``."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path(
        "valoracion/",
        views.InventoryValuationView.as_view(),
        name="inventory-valuation",
    ),
    path(
        "api/chart/movements/",
        views.ChartDataView.as_view(),
        name="chart-movements",
    ),
]
