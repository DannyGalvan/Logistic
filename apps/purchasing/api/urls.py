"""Rutas API de ``purchasing``."""

from __future__ import annotations

from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("purchase-orders", views.PurchaseOrderViewSet)

urlpatterns = router.urls
