"""URLs de la app ``catalog``."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("categorias/", views.CategoryListView.as_view(), name="category-list"),
    path(
        "categorias/nueva/",
        views.CategoryCreateView.as_view(),
        name="category-create",
    ),
    path(
        "categorias/<int:pk>/editar/",
        views.CategoryUpdateView.as_view(),
        name="category-update",
    ),
    path("marcas/", views.BrandListView.as_view(), name="brand-list"),
    path(
        "marcas/nueva/",
        views.BrandCreateView.as_view(),
        name="brand-create",
    ),
    path(
        "marcas/<int:pk>/editar/",
        views.BrandUpdateView.as_view(),
        name="brand-update",
    ),
    path("unidades/", views.UnitListView.as_view(), name="unit-list"),
    path(
        "unidades/nueva/",
        views.UnitCreateView.as_view(),
        name="unit-create",
    ),
    path(
        "unidades/<int:pk>/editar/",
        views.UnitUpdateView.as_view(),
        name="unit-update",
    ),
    path("productos/", views.ProductListView.as_view(), name="product-list"),
    path(
        "productos/nuevo/",
        views.ProductCreateView.as_view(),
        name="product-create",
    ),
    path(
        "productos/<int:pk>/editar/",
        views.ProductUpdateView.as_view(),
        name="product-update",
    ),
    path(
        "productos/<int:pk>/desactivar/",
        views.ProductDeactivateView.as_view(),
        name="product-deactivate",
    ),
]
