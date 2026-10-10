"""Rutas API de ``sales``."""

from __future__ import annotations

from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("sales-orders", views.SalesOrderViewSet)

urlpatterns = router.urls
