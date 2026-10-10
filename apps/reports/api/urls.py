"""Rutas API de ``reports``."""

from __future__ import annotations

from django.urls import path

from . import views

urlpatterns = [
    path("reports/kpis/", views.KpiView.as_view(), name="reports-kpis"),
]
