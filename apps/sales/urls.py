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
    path("<int:pk>/", views.SalesOrderDetailView.as_view(), name="order-detail"),
    path(
        "<int:pk>/lineas/",
        views.SalesOrderAddLineView.as_view(),
        name="order-add-line",
    ),
    path(
        "<int:pk>/confirmar/",
        views.SalesOrderConfirmView.as_view(),
        name="order-confirm",
    ),
    path(
        "<int:pk>/cancelar/",
        views.SalesOrderCancelView.as_view(),
        name="order-cancel",
    ),
    path(
        "<int:pk>/despachar/",
        views.SalesOrderShipView.as_view(),
        name="order-ship",
    ),
]
