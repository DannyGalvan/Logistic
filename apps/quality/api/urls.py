"""Rutas API de ``quality``."""

from __future__ import annotations

from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("lint-runs", views.LintRunViewSet)

urlpatterns = router.urls
