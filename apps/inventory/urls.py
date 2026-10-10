"""URLs de la app ``inventory``."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("stock/", views.StockListView.as_view(), name="stock-list"),
    path("movimientos/", views.MovementListView.as_view(), name="movement-list"),
    path("entrada/", views.ReceiveView.as_view(), name="receive"),
    path("salida/", views.IssueView.as_view(), name="issue"),
    path(
        "transferencia/",
        views.TransferView.as_view(),
        name="transfer",
    ),
    path("ajuste/", views.AdjustView.as_view(), name="adjust"),
    path("alertas/", views.AlertListView.as_view(), name="alert-list"),
    path("lotes/", views.LotListView.as_view(), name="lot-list"),
    path(
        "conteos/",
        views.CycleCountListView.as_view(),
        name="cycle-count-list",
    ),
    path(
        "conteos/nuevo/",
        views.CycleCountCreateView.as_view(),
        name="cycle-count-create",
    ),
    path(
        "conteos/<int:pk>/",
        views.CycleCountDetailView.as_view(),
        name="cycle-count-detail",
    ),
    path(
        "conteos/<int:pk>/iniciar/",
        views.CycleCountStartView.as_view(),
        name="cycle-count-start",
    ),
    path(
        "conteos/<int:pk>/registrar/",
        views.CycleCountRecordView.as_view(),
        name="cycle-count-record",
    ),
    path(
        "conteos/<int:pk>/aprobar/",
        views.CycleCountApproveView.as_view(),
        name="cycle-count-approve",
    ),
    path(
        "conteos/<int:pk>/cancelar/",
        views.CycleCountCancelView.as_view(),
        name="cycle-count-cancel",
    ),
    path("kardex/", views.KardexView.as_view(), name="kardex"),
]
