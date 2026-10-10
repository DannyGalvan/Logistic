"""URLs de la app ``quality``."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "quality"

urlpatterns = [
    path("", views.QualityDashboardView.as_view(), name="dashboard"),
    path("corridas/", views.LintRunListView.as_view(), name="run-list"),
    path(
        "corridas/<int:pk>/",
        views.LintRunDetailView.as_view(),
        name="run-detail",
    ),
    path("analizar/", views.SnippetAnalyzeView.as_view(), name="snippet"),
    path("catalogo/", views.CatalogView.as_view(), name="catalog"),
    path("ejecutar/", views.RunPylintView.as_view(), name="run"),
]
