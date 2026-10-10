"""Enrutador de la API REST v1.

Cada app expone su ``api/urls.py``; aqui solo se agregan bajo
``/api/v1/`` junto con el esquema OpenAPI y Swagger.
"""

from __future__ import annotations

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_v1_patterns = [
    path("auth/", include("apps.accounts.api.urls")),
    path("", include("apps.catalog.api.urls")),
    path("", include("apps.warehouses.api.urls")),
    path("", include("apps.partners.api.urls")),
    path("", include("apps.inventory.api.urls")),
    path("", include("apps.purchasing.api.urls")),
    path("", include("apps.sales.api.urls")),
    path("", include("apps.quality.api.urls")),
    path("", include("apps.reports.api.urls")),
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
