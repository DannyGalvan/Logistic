"""Enrutador raiz del proyecto."""

from __future__ import annotations

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("apps.accounts.urls")),
    path("catalogo/", include("apps.catalog.urls")),
    path("almacenes/", include("apps.warehouses.urls")),
    path("socios/", include("apps.partners.urls")),
    path("inventario/", include("apps.inventory.urls")),
    path("compras/", include("apps.purchasing.urls")),
    path("ventas/", include("apps.sales.urls")),
    path("reportes/", include("apps.reports.urls")),
    path("auditoria/", include("apps.audit.urls")),
    path("calidad/", include("apps.quality.urls")),
    path("", include("apps.core.urls")),
    path("", include("config.api_urls")),
]

if "debug_toolbar" in settings.INSTALLED_APPS:
    urlpatterns = [path("__debug__/", include("debug_toolbar.urls")), *urlpatterns]

handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
