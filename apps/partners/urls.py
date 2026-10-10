"""URLs de la app ``partners``."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "partners"

urlpatterns = [
    path("proveedores/", views.SupplierListView.as_view(), name="supplier-list"),
    path(
        "proveedores/nuevo/",
        views.SupplierCreateView.as_view(),
        name="supplier-create",
    ),
    path(
        "proveedores/<int:pk>/editar/",
        views.SupplierUpdateView.as_view(),
        name="supplier-update",
    ),
    path("clientes/", views.CustomerListView.as_view(), name="customer-list"),
    path(
        "clientes/nuevo/",
        views.CustomerCreateView.as_view(),
        name="customer-create",
    ),
    path(
        "clientes/<int:pk>/editar/",
        views.CustomerUpdateView.as_view(),
        name="customer-update",
    ),
]
