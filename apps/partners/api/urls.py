"""Rutas API de ``partners``."""

from __future__ import annotations

from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("suppliers", views.SupplierViewSet)
router.register("customers", views.CustomerViewSet)

urlpatterns = router.urls
