"""Vistas web de ``inventory``.

Vistas de movimiento (entrada / salida / transferencia / ajuste),
historial de movimientos, kardex, alertas, lotes y conteos.
"""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView

from apps.catalog.models import Product
from apps.core.views import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ServiceActionView,
    parse_date,
    parse_decimal,
)
from apps.warehouses.models import Warehouse

from . import selectors, services
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

    permission_required = "inventory.view_stockmovement"
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
        return HttpResponseRedirect(cycle.get_absolute_url())


class CycleCountDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView,
):
    """Detalle del conteo con captura de cantidades."""

    permission_required = "inventory.view_cyclecount"
    model = CycleCount
    template_name = "inventory/cycle_count_detail.html"
    context_object_name = "cycle"
    raise_exception = True

    def get_context_data(self, **kwargs):  # type: ignore[no-untyped-def]
        """Agrega las lineas del conteo."""
        context = super().get_context_data(**kwargs)
        lines = list(
            self.object.lines.select_related("product", "location", "lot")
            .order_by("location__code", "product__sku")
        )
        context["lines"] = lines
        context["all_counted"] = bool(lines) and all(
            line.counted_quantity is not None for line in lines
        )
        return context


class CycleCountStartView(ServiceActionView):
    """Pasa el conteo a ``IN_PROGRESS``."""

    permission_required = "inventory.add_cyclecount"
    model = CycleCount
    success_message = "Conteo iniciado."

    def perform(self, obj, request) -> None:
        """Delegado al service."""
        services.CycleCountService().start(obj)


class CycleCountRecordView(ServiceActionView):
    """Guarda las cantidades contadas."""

    permission_required = "inventory.add_cyclecount"
    model = CycleCount
    success_message = "Cantidades guardadas."

    def perform(self, obj, request) -> None:
        """Registra cada linea con cantidad capturada."""
        service = services.CycleCountService()
        for line in obj.lines.all():
            counted = parse_decimal(request.POST.get(f"count_{line.pk}"))
            if counted is not None and counted >= 0:
                service.record(line, counted)


class CycleCountApproveView(ServiceActionView):
    """Aprueba el conteo y genera los ajustes."""

    permission_required = "accounts.approve_cyclecount"
    model = CycleCount
    success_message = "Conteo aprobado; ajustes generados."

    def perform(self, obj, request) -> None:
        """Delegado al service."""
        services.CycleCountService().approve(obj, user=request.user)


class CycleCountCancelView(ServiceActionView):
    """Cancela el conteo."""

    permission_required = "inventory.add_cyclecount"
    model = CycleCount
    success_message = "Conteo cancelado."

    def perform(self, obj, request) -> None:
        """Delegado al service."""
        services.CycleCountService().cancel(obj)


class KardexView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Kardex valorizado de un producto."""

    permission_required = "accounts.view_kardex"
    template_name = "inventory/kardex.html"
    context_object_name = "rows"
    raise_exception = True
    product: Product | None = None
    warehouse: Warehouse | None = None

    def get_queryset(self):  # type: ignore[no-untyped-def]
        """Calcula el kardex segun los filtros del querystring."""
        params = self.request.GET
        self.product = Product.objects.filter(pk=params.get("product") or 0).first()
        self.warehouse = Warehouse.objects.filter(
            pk=params.get("warehouse") or 0
        ).first()
        if self.product is None:
            return []
        return selectors.kardex(
            self.product,
            warehouse=self.warehouse,
            date_from=parse_date(params.get("desde")),
            date_to=parse_date(params.get("hasta")),
        )

    def get_context_data(self, **kwargs):  # type: ignore[no-untyped-def]
        """Agrega los catalogos para los filtros."""
        context = super().get_context_data(**kwargs)
        context["product"] = self.product
        context["warehouse"] = self.warehouse
        context["products"] = Product.objects.order_by("sku").only("pk", "sku", "name")
        context["warehouses"] = Warehouse.objects.order_by("code")
        return context


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
    "CycleCountDetailView",
    "CycleCountStartView",
    "CycleCountRecordView",
    "CycleCountApproveView",
    "CycleCountCancelView",
    "KardexView",
]
