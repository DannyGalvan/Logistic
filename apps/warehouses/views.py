"""Vistas web de la app ``warehouses``."""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from . import services, selectors
from .forms import LocationForm, WarehouseForm
from .models import Location, Warehouse


class WarehouseListView(ListView):
    """Listado de almacenes."""

    model = Warehouse
    template_name = "warehouses/warehouse_list.html"
    context_object_name = "warehouses"
    paginate_by = 20

    def get_queryset(self):
        """Aplica selector active."""
        return selectors.active_warehouses()


class WarehouseCreateView(CreateView):  # pylint: disable=too-few-public-methods
    """Alta de almacen (crea ubicaciones por defecto)."""

    model = Warehouse
    form_class = WarehouseForm
    template_name = "warehouses/warehouse_form.html"
    success_url = reverse_lazy("warehouses:warehouse-list")

    def form_valid(self, form):
        """Llama al service con el usuario autenticado."""
        self.object = services.create_warehouse(  # pylint: disable=attribute-defined-outside-init
            user=self.request.user, **form.cleaned_data
        )
        messages.success(
            self.request, f"Almacen '{self.object.code}' creado con ubicaciones."
        )
        return HttpResponseRedirect(self.get_success_url())


class WarehouseUpdateView(UpdateView):
    """Edicion de almacen."""

    model = Warehouse
    form_class = WarehouseForm
    template_name = "warehouses/warehouse_form.html"
    success_url = reverse_lazy("warehouses:warehouse-list")


class LocationCreateView(CreateView):
    """Alta de ubicacion dentro de un almacen."""

    model = Location
    form_class = LocationForm
    template_name = "warehouses/location_form.html"

    def __init__(self, **kwargs):
        """Inicializa el atributo ``warehouse`` antes del dispatch."""
        super().__init__(**kwargs)
        self.warehouse: Warehouse | None = None

    def dispatch(self, request, *args, **kwargs):
        """Captura el almacen desde la URL."""
        self.warehouse = get_object_or_404(Warehouse, pk=kwargs["warehouse_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Expone el almacen al template."""
        context = super().get_context_data(**kwargs)
        context["warehouse"] = self.warehouse
        return context

    def form_valid(self, form):
        """Llama al service y guarda la FK del almacen."""
        location = services.create_location(
            warehouse=self.warehouse, **form.cleaned_data
        )
        messages.success(
            self.request, f"Ubicacion '{location.code}' creada."
        )
        return HttpResponseRedirect(
            reverse_lazy(
                "warehouses:warehouse-update", args=[self.warehouse.pk]
            )
        )


__all__ = [
    "WarehouseListView",
    "WarehouseCreateView",
    "WarehouseUpdateView",
    "LocationCreateView",
]
