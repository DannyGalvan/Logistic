"""Vistas web de ``sales``."""

from __future__ import annotations

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.exceptions import DomainError
from apps.core.views import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ServiceActionView,
    error_text,
    form_errors_text,
    parse_decimal,
)
from apps.inventory.models import Lot
from apps.warehouses.models import Location

from . import services
from .forms import SalesOrderForm, SalesOrderLineForm
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

    def form_valid(self, form):
        """Crea la orden via service."""
        order = services.SalesService().create_order(
            user=self.request.user, **form.cleaned_data
        )
        messages.success(self.request, f"Orden {order.code} creada.")
        return HttpResponseRedirect(order.get_absolute_url())


class SalesOrderUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView,
):
    """Edicion de orden de venta."""

    permission_required = "sales.change_salesorder"
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = "sales/order_form.html"
    raise_exception = True

    def get_queryset(self):
        """Solo se editan ordenes en borrador."""
        return SalesOrder.objects.filter(status=SalesOrder.Status.DRAFT)

    def get_success_url(self) -> str:
        """Vuelve al detalle de la orden."""
        return self.object.get_absolute_url()


class SalesOrderDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView,
):
    """Detalle de la orden con picking sugerido y despachos."""

    permission_required = "sales.view_salesorder"
    model = SalesOrder
    template_name = "sales/order_detail.html"
    context_object_name = "order"
    raise_exception = True

    def get_queryset(self):
        """Precarga relaciones usadas en la plantilla."""
        return SalesOrder.objects.select_related("customer", "warehouse")

    def get_context_data(self, **kwargs):  # type: ignore[no-untyped-def]
        """Agrega lineas, despachos y la sugerencia de picking."""
        context = super().get_context_data(**kwargs)
        order = self.object
        context["lines"] = order.lines.select_related("product")
        context["shipments"] = order.shipments.prefetch_related(
            "lines__order_line__product", "lines__location", "lines__lot"
        )
        context["line_form"] = SalesOrderLineForm()
        context["can_ship"] = order.status in (
            SalesOrder.Status.CONFIRMED,
            SalesOrder.Status.PARTIALLY_SHIPPED,
        )
        if context["can_ship"]:
            context["picking"], context["picking_error"] = _picking_rows(order)
        return context


def _picking_rows(order: SalesOrder) -> tuple[list[dict], str]:
    """Devuelve la sugerencia de picking enriquecida para la plantilla."""
    try:
        suggestions = services.SalesService().suggest_picking(order)
    except (DomainError, ValidationError) as exc:
        return [], error_text(exc)
    lines = {line.pk: line for line in order.lines.select_related("product")}
    locations = Location.objects.in_bulk({row["location_id"] for row in suggestions})
    lots = Lot.objects.in_bulk(
        {row["lot_id"] for row in suggestions if row["lot_id"]}
    )
    rows = [
        {
            **row,
            "product": lines[row["order_line_id"]].product,
            "location": locations.get(row["location_id"]),
            "lot": lots.get(row["lot_id"]),
        }
        for row in suggestions
    ]
    return rows, ""


class SalesOrderAddLineView(ServiceActionView):
    """Agrega una linea a la orden en borrador."""

    permission_required = "sales.change_salesorder"
    model = SalesOrder
    success_message = "Linea agregada."

    def perform(self, obj, request) -> None:
        """Valida el formulario y delega en el service."""
        form = SalesOrderLineForm(request.POST)
        if not form.is_valid():
            raise ValidationError(form_errors_text(form))
        services.SalesService().add_line(obj, **form.cleaned_data)


class SalesOrderConfirmView(ServiceActionView):
    """Confirma la orden."""

    permission_required = "accounts.confirm_salesorder"
    model = SalesOrder
    success_message = "Orden confirmada."

    def perform(self, obj, request) -> None:
        """Delegado al service."""
        services.SalesService().confirm(obj)


class SalesOrderCancelView(ServiceActionView):
    """Cancela la orden."""

    permission_required = "sales.change_salesorder"
    model = SalesOrder
    success_message = "Orden cancelada."

    def perform(self, obj, request) -> None:
        """Delegado al service."""
        services.SalesService().cancel(obj)


class SalesOrderShipView(ServiceActionView):
    """Registra un despacho a partir de las filas de picking."""

    permission_required = "accounts.ship_salesorder"
    model = SalesOrder
    success_message = "Despacho registrado."

    def perform(self, obj, request) -> None:
        """Construye los DTO de despacho desde el POST."""
        lines = []
        for idx in request.POST.getlist("row"):
            quantity = parse_decimal(request.POST.get(f"qty_{idx}"))
            if quantity is None or quantity <= 0:
                continue
            lot_id = request.POST.get(f"lot_{idx}") or None
            lines.append(
                services.ShipLineInput(
                    order_line_id=int(request.POST[f"line_{idx}"]),
                    location_id=int(request.POST[f"location_{idx}"]),
                    lot_id=int(lot_id) if lot_id else None,
                    quantity=quantity,
                )
            )
        if not lines:
            raise ValidationError("Indica al menos una cantidad a despachar.")
        services.SalesService().ship(
            obj,
            lines=lines,
            user=request.user,
            carrier=request.POST.get("carrier", "").strip(),
            tracking_number=request.POST.get("tracking_number", "").strip(),
        )


__all__ = [
    "SalesOrderListView",
    "SalesOrderCreateView",
    "SalesOrderUpdateView",
    "SalesOrderDetailView",
    "SalesOrderAddLineView",
    "SalesOrderConfirmView",
    "SalesOrderCancelView",
    "SalesOrderShipView",
]
