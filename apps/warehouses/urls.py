"""URLs de la app ``warehouses``."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "warehouses"

urlpatterns = [
    path("", views.WarehouseListView.as_view(), name="warehouse-list"),
    path(
        "nuevo/",
        views.WarehouseCreateView.as_view(),
        name="warehouse-create",
    ),
    path(
        "<int:pk>/editar/",
        views.WarehouseUpdateView.as_view(),
        name="warehouse-update",
    ),
    path(
        "<int:warehouse_pk>/ubicaciones/nueva/",
        views.LocationCreateView.as_view(),
        name="location-create",
    ),
]
