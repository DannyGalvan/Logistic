"""Enrutador de la API REST v1."""

from __future__ import annotations

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_v1_patterns = [
    path("auth/", include("apps.accounts.api.urls")),
]

urlpatterns = [
    path("api/v1/", include((api_v1_patterns, "api"), namespace="v1")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger",
    ),
]
