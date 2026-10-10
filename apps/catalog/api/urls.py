"""Rutas API de ``catalog``."""

from __future__ import annotations

from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("categories", views.CategoryViewSet)
router.register("brands", views.BrandViewSet)
router.register("uoms", views.UnitOfMeasureViewSet)
router.register("products", views.ProductViewSet)

urlpatterns = router.urls
