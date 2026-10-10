"""Vistas web de ``purchasing``."""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from apps.core.views import LoginRequiredMixin, PermissionRequiredMixin

from . import services
from .forms import PurchaseOrderForm
from .models import PurchaseOrder


class PurchaseOrderListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Listado de ordenes de compra."""

    permission_required = "purchasing.view_purchaseorder"
    template_name = "purchasing/order_list.html"
    context_object_name = "orders"
    paginate_by = 20
    queryset = PurchaseOrder.objects.order_by("-code")


class PurchaseOrderCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView,
):
    """Alta de orden."""

    permission_required = "purchasing.add_purchaseorder"
    form_class = PurchaseOrderForm
    template_name = "purchasing/order_form.html"
    success_url = reverse_lazy("purchasing:order-list")

    def form_valid(self, form):
        """Crea la orden via service."""
        order = services.PurchaseService().create_order(
            user=self.request.user, **form.cleaned_data
        )
        messages.success(self.request, f"Orden {order.code} creada.")
        return HttpResponseRedirect(
            reverse_lazy("purchasing:order-update", args=[order.pk])
        )


class PurchaseOrderUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView,
):
    """Edicion de orden (solo en DRAFT)."""

    permission_required = "purchasing.change_purchaseorder"
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = "purchasing/order_form.html"
    success_url = reverse_lazy("purchasing:order-list")


__all__ = [
    "PurchaseOrderListView",
    "PurchaseOrderCreateView",
    "PurchaseOrderUpdateView",
]
