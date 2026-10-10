"""Vistas web de ``inventory``.

Vistas de movimiento (entrada / salida / transferencia / ajuste),
historial de movimientos, kardex, alertas, lotes y conteos.
"""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, ListView

from apps.core.views import LoginRequiredMixin, PermissionRequiredMixin

from . import services
from .forms import AdjustForm, CycleCountForm, IssueForm, ReceiveForm, TransferForm
from .models import Alert, CycleCount, Lot, Stock, StockMovement


class StockListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Listado de existencias."""

    permission_required = "inventory.view_stock"
    template_name = "inventory/stock_list.html"
    context_object_name = "stocks"
    paginate_by = 20

    def get_queryset(self):
        """Filtra por producto o ubicacion."""
        qs = Stock.objects.select_related("product", "location", "lot")
        product = self.request.GET.get("product")
        location = self.request.GET.get("location")
        if product:
            qs = qs.filter(product_id=product)
        if location:
            qs = qs.filter(location_id=location)
        return qs


class MovementListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Historial de movimientos."""

    permission_required = "inventory.view_movement"
    template_name = "inventory/movement_list.html"
    context_object_name = "movements"
    paginate_by = 30
    queryset = StockMovement.objects.select_related(
        "product", "lot", "from_location", "to_location", "created_by"
    ).order_by("-created_at")


class _MovementCreateView(  # pylint: disable=too-few-public-methods
    LoginRequiredMixin, PermissionRequiredMixin, FormView
):
    """Clase base para formularios de stock."""

    raise_exception = True
    method_name: str = ""

    def get_service(self):
        """Devuelve el ``InventoryService`` (inyeccion)."""
        return services.InventoryService()

    def get_service_kwargs(self, data: dict) -> dict:
        """Adapta ``cleaned_data`` a la firma del metodo del service."""
        return dict(data)

    def form_valid(self, form):
        """Llama al service y muestra feedback."""
        data = self.get_service_kwargs(form.cleaned_data)
        method = getattr(self.get_service(), self.method_name)
        try:
            method(user=self.request.user, **data)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Operacion registrada.")
        return HttpResponseRedirect(self.get_success_url())


class ReceiveView(_MovementCreateView):
    """Vista de recepcion de stock."""

    permission_required = "inventory.add_stockmovement"
    form_class = ReceiveForm
    template_name = "inventory/receive_form.html"
    success_url = reverse_lazy("inventory:movement-list")
    method_name = "receive"

    def get_service_kwargs(self, data: dict) -> dict:
        """``warehouse`` solo filtra ubicaciones; no va al service."""
        data = dict(data)
        data.pop("warehouse", None)
        return data


class IssueView(_MovementCreateView):
    """Vista de salida de stock."""

    permission_required = "inventory.add_stockmovement"
    form_class = IssueForm
    template_name = "inventory/issue_form.html"
    success_url = reverse_lazy("inventory:movement-list")
    method_name = "issue"


class TransferView(_MovementCreateView):
    """Vista de transferencia."""

    permission_required = "inventory.add_stockmovement"
    form_class = TransferForm
    template_name = "inventory/transfer_form.html"
    success_url = reverse_lazy("inventory:movement-list")
    method_name = "transfer"

    def get_service_kwargs(self, data: dict) -> dict:
        """El form usa ``location`` como origen."""
        data = dict(data)
        data["from_location"] = data.pop("location")
        return data


class AdjustView(_MovementCreateView):
    """Vista de ajuste."""

    permission_required = "inventory.add_stockmovement"
    form_class = AdjustForm
    template_name = "inventory/adjust_form.html"
    success_url = reverse_lazy("inventory:movement-list")
    method_name = "adjust"

    def get_service_kwargs(self, data: dict) -> dict:
        """El ajuste usa ``counted_quantity`` y ``note``."""
        data = dict(data)
        data.pop("quantity", None)
        data["note"] = data.pop("reference", "")
        return data


class AlertListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Listado de alertas."""

    permission_required = "inventory.view_alert"
    template_name = "inventory/alert_list.html"
    context_object_name = "alerts"
    paginate_by = 30
    queryset = Alert.objects.order_by("-created_at")


class LotListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Listado de lotes."""

    permission_required = "inventory.view_stock"
    template_name = "inventory/lot_list.html"
    context_object_name = "lots"
    paginate_by = 30
    queryset = Lot.objects.select_related("product")


class CycleCountListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Listado de conteos ciclicos."""

    permission_required = "inventory.view_cyclecount"
    template_name = "inventory/cycle_count_list.html"
    context_object_name = "cycle_counts"
    paginate_by = 20
    queryset = CycleCount.objects.order_by("-code")


class CycleCountCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Alta de un conteo ciclico."""

    permission_required = "inventory.add_cyclecount"
    form_class = CycleCountForm
    template_name = "inventory/cycle_count_form.html"
    success_url = reverse_lazy("inventory:cycle-count-list")
    raise_exception = True

    def form_valid(self, form):
        """Crea el conteo via service."""
        svc = services.CycleCountService()
        cycle = svc.create(
            warehouse=form.cleaned_data["warehouse"],
            user=self.request.user,
            location=form.cleaned_data.get("location"),
        )
        messages.success(self.request, f"Conteo {cycle.code} creado.")
        return HttpResponseRedirect(self.success_url)


__all__ = [
    "StockListView",
    "MovementListView",
    "ReceiveView",
    "IssueView",
    "TransferView",
    "AdjustView",
    "AlertListView",
    "LotListView",
    "CycleCountListView",
    "CycleCountCreateView",
]
