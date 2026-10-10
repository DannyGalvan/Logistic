"""Rutas API de ``warehouses``."""

from __future__ import annotations

from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("warehouses", views.WarehouseViewSet)
router.register("locations", views.LocationViewSet)

urlpatterns = router.urls
