"""URLs de la app ``sales``."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "sales"

urlpatterns = [
    path("", views.SalesOrderListView.as_view(), name="order-list"),
    path(
        "nueva/",
        views.SalesOrderCreateView.as_view(),
        name="order-create",
    ),
    path(
        "<int:pk>/editar/",
        views.SalesOrderUpdateView.as_view(),
        name="order-update",
    ),
]
