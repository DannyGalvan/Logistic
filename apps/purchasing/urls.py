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
    path("<int:pk>/", views.PurchaseOrderDetailView.as_view(), name="order-detail"),
    path(
        "<int:pk>/lineas/",
        views.PurchaseOrderAddLineView.as_view(),
        name="order-add-line",
    ),
    path(
        "<int:pk>/confirmar/",
        views.PurchaseOrderConfirmView.as_view(),
        name="order-confirm",
    ),
    path(
        "<int:pk>/cancelar/",
        views.PurchaseOrderCancelView.as_view(),
        name="order-cancel",
    ),
    path(
        "<int:pk>/recibir/",
        views.PurchaseOrderReceiveView.as_view(),
        name="order-receive",
    ),
]
