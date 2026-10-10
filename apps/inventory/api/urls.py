"""Rutas API de ``inventory``."""

from __future__ import annotations

from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("lots", views.LotViewSet)
router.register("stock", views.StockViewSet)
router.register("movements", views.StockMovementViewSet)
router.register("cycle-counts", views.CycleCountViewSet)

urlpatterns = router.urls
