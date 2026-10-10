"""Vistas web de ``sales``."""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from apps.core.views import LoginRequiredMixin, PermissionRequiredMixin

from . import services
from .forms import SalesOrderForm
from .models import SalesOrder


class SalesOrderListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Listado de ordenes de venta."""

    permission_required = "sales.view_salesorder"
    template_name = "sales/order_list.html"
    context_object_name = "orders"
    paginate_by = 20
    queryset = SalesOrder.objects.order_by("-code")


class SalesOrderCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView,
):
    """Alta de orden de venta."""

    permission_required = "sales.add_salesorder"
    form_class = SalesOrderForm
    template_name = "sales/order_form.html"
    success_url = reverse_lazy("sales:order-list")

    def form_valid(self, form):
        """Crea la orden via service."""
        order = services.SalesService().create_order(
            user=self.request.user, **form.cleaned_data
        )
        messages.success(self.request, f"Orden {order.code} creada.")
        return HttpResponseRedirect(
            reverse_lazy("sales:order-update", args=[order.pk])
        )


class SalesOrderUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView,
):
    """Edicion de orden de venta."""

    permission_required = "sales.change_salesorder"
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = "sales/order_form.html"
    success_url = reverse_lazy("sales:order-list")


__all__ = [
    "SalesOrderListView",
    "SalesOrderCreateView",
    "SalesOrderUpdateView",
]
