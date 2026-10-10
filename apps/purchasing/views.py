"""Vistas web de ``purchasing``."""

from __future__ import annotations

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.views import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ServiceActionView,
    form_errors_text,
    parse_date,
    parse_decimal,
)
from apps.warehouses.models import Location

from . import services
from .forms import PurchaseOrderForm, PurchaseOrderLineForm
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

    def form_valid(self, form):
        """Crea la orden via service."""
        order = services.PurchaseService().create_order(
            user=self.request.user, **form.cleaned_data
        )
        messages.success(self.request, f"Orden {order.code} creada.")
        return HttpResponseRedirect(order.get_absolute_url())


class PurchaseOrderUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView,
):
    """Edicion de orden (solo en DRAFT)."""

    permission_required = "purchasing.change_purchaseorder"
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = "purchasing/order_form.html"
    raise_exception = True

    def get_queryset(self):
        """Solo se editan ordenes en borrador."""
        return PurchaseOrder.objects.filter(status=PurchaseOrder.Status.DRAFT)

    def get_success_url(self) -> str:
        """Vuelve al detalle de la orden."""
        return self.object.get_absolute_url()


class PurchaseOrderDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView,
):
    """Detalle de la orden con lineas, recepciones y acciones."""

    permission_required = "purchasing.view_purchaseorder"
    model = PurchaseOrder
    template_name = "purchasing/order_detail.html"
    context_object_name = "order"
    raise_exception = True

    def get_queryset(self):
        """Precarga relaciones usadas en la plantilla."""
        return PurchaseOrder.objects.select_related("supplier", "warehouse")

    def get_context_data(self, **kwargs):  # type: ignore[no-untyped-def]
        """Agrega lineas, formulario de linea y ubicaciones de recepcion."""
        context = super().get_context_data(**kwargs)
        order = self.object
        context["lines"] = order.lines.select_related("product")
        context["receipts"] = order.receipts.prefetch_related(
            "lines__order_line__product"
        ).select_related("location")
        context["line_form"] = PurchaseOrderLineForm()
        context["locations"] = Location.objects.filter(
            warehouse=order.warehouse, is_active=True
        ).order_by("code")
        context["can_receive"] = order.status in (
            PurchaseOrder.Status.CONFIRMED,
            PurchaseOrder.Status.PARTIALLY_RECEIVED,
        )
        return context


class PurchaseOrderAddLineView(ServiceActionView):
    """Agrega una linea a la orden en borrador."""

    permission_required = "purchasing.change_purchaseorder"
    model = PurchaseOrder
    success_message = "Linea agregada."

    def perform(self, obj, request) -> None:
        """Valida el formulario y delega en el service."""
        form = PurchaseOrderLineForm(request.POST)
        if not form.is_valid():
            raise ValidationError(form_errors_text(form))
        services.PurchaseService().add_line(obj, **form.cleaned_data)


class PurchaseOrderConfirmView(ServiceActionView):
    """Confirma la orden."""

    permission_required = "accounts.confirm_purchaseorder"
    model = PurchaseOrder
    success_message = "Orden confirmada."

    def perform(self, obj, request) -> None:
        """Delegado al service."""
        services.PurchaseService().confirm(obj)


class PurchaseOrderCancelView(ServiceActionView):
    """Cancela la orden."""

    permission_required = "purchasing.change_purchaseorder"
    model = PurchaseOrder
    success_message = "Orden cancelada."

    def perform(self, obj, request) -> None:
        """Delegado al service."""
        services.PurchaseService().cancel(obj)


class PurchaseOrderReceiveView(ServiceActionView):
    """Registra una recepcion parcial o total."""

    permission_required = "accounts.receive_purchaseorder"
    model = PurchaseOrder
    success_message = "Recepcion registrada."

    def perform(self, obj, request) -> None:
        """Construye los DTO de recepcion desde el POST."""
        location = Location.objects.filter(
            pk=request.POST.get("location") or 0, warehouse=obj.warehouse
        ).first()
        if location is None:
            raise ValidationError("Selecciona una ubicacion de recepcion.")
        lines = []
        for line in obj.lines.all():
            quantity = parse_decimal(request.POST.get(f"qty_{line.pk}"))
            if quantity is None or quantity <= 0:
                continue
            lines.append(
                services.ReceiptLineInput(
                    order_line_id=line.pk,
                    quantity=quantity,
                    lot_number=request.POST.get(f"lot_{line.pk}", "").strip(),
                    expires_at=parse_date(request.POST.get(f"exp_{line.pk}")),
                )
            )
        if not lines:
            raise ValidationError("Indica al menos una cantidad a recibir.")
        services.PurchaseService().receive(
            obj, location=location, lines=lines, user=request.user
        )


__all__ = [
    "PurchaseOrderListView",
    "PurchaseOrderCreateView",
    "PurchaseOrderUpdateView",
    "PurchaseOrderDetailView",
    "PurchaseOrderAddLineView",
    "PurchaseOrderConfirmView",
    "PurchaseOrderCancelView",
    "PurchaseOrderReceiveView",
]
