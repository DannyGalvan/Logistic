"""URLs de la app ``purchasing``."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "purchasing"

urlpatterns = [
    path("", views.PurchaseOrderListView.as_view(), name="order-list"),
    path(
        "nueva/",
        views.PurchaseOrderCreateView.as_view(),
        name="order-create",
    ),
    path(
        "<int:pk>/editar/",
        views.PurchaseOrderUpdateView.as_view(),
        name="order-update",
    ),
]
