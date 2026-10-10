"""Vistas web de la app ``partners``."""

from __future__ import annotations

from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from . import selectors, services
from .forms import CustomerForm, SupplierForm
from .models import Customer, Supplier


class SupplierListView(ListView):
    """Listado de proveedores."""

    model = Supplier
    template_name = "partners/supplier_list.html"
    context_object_name = "suppliers"
    paginate_by = 20

    def get_queryset(self):
        """Aplica selector active."""
        return selectors.active_suppliers()


class SupplierCreateView(CreateView):
    """Alta de proveedor."""

    model = Supplier
    form_class = SupplierForm
    template_name = "partners/supplier_form.html"
    success_url = reverse_lazy("partners:supplier-list")

    def form_valid(self, form):
        """Llama al service."""
        self.object = services.create_supplier(  # pylint: disable=attribute-defined-outside-init
            user=self.request.user, **form.cleaned_data
        )
        return HttpResponseRedirect(self.get_success_url())


class SupplierUpdateView(UpdateView):
    """Edicion de proveedor."""

    model = Supplier
    form_class = SupplierForm
    template_name = "partners/supplier_form.html"
    success_url = reverse_lazy("partners:supplier-list")


class CustomerListView(ListView):
    """Listado de clientes."""

    model = Customer
    template_name = "partners/customer_list.html"
    context_object_name = "customers"
    paginate_by = 20

    def get_queryset(self):
        """Aplica selector active."""
        return selectors.active_customers()


class CustomerCreateView(CreateView):
    """Alta de cliente."""

    model = Customer
    form_class = CustomerForm
    template_name = "partners/customer_form.html"
    success_url = reverse_lazy("partners:customer-list")

    def form_valid(self, form):
        """Llama al service."""
        self.object = services.create_customer(  # pylint: disable=attribute-defined-outside-init
            user=self.request.user, **form.cleaned_data
        )
        return HttpResponseRedirect(self.get_success_url())


class CustomerUpdateView(UpdateView):
    """Edicion de cliente."""

    model = Customer
    form_class = CustomerForm
    template_name = "partners/customer_form.html"
    success_url = reverse_lazy("partners:customer-list")


__all__ = [
    "SupplierListView",
    "SupplierCreateView",
    "SupplierUpdateView",
    "CustomerListView",
    "CustomerCreateView",
    "CustomerUpdateView",
]
