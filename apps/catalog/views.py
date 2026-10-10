"""Vistas web de la app ``catalog``.

CRUD para ``Category``, ``Brand``, ``UnitOfMeasure`` y ``Product``.
Las vistas de lectura usan ``selectors``; las de escritura delegan en
``services``.
"""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    UpdateView,
)

from . import services, selectors
from .forms import BrandForm, CategoryForm, ProductForm, UnitForm
from .models import Brand, Category, Product, UnitOfMeasure


class _BaseCatalogListView(ListView):
    """Clase base para los listados."""

    paginate_by = 20


class CategoryListView(_BaseCatalogListView):
    """Listado de categorias."""

    model = Category
    template_name = "catalog/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        """Usa el selector ``active_categories``."""
        return selectors.active_categories()


class CategoryCreateView(CreateView):
    """Alta de categoria."""

    model = Category
    form_class = CategoryForm
    template_name = "catalog/category_form.html"
    success_url = reverse_lazy("catalog:category-list")

    def form_valid(self, form):
        """Llama al service y muestra feedback."""
        self.object = services.create_category(  # pylint: disable=attribute-defined-outside-init
            **form.cleaned_data
        )
        messages.success(self.request, f"Categoria '{self.object.name}' creada.")
        return HttpResponseRedirect(self.get_success_url())


class CategoryUpdateView(UpdateView):
    """Edicion de categoria."""

    model = Category
    form_class = CategoryForm
    template_name = "catalog/category_form.html"
    success_url = reverse_lazy("catalog:category-list")


class BrandListView(_BaseCatalogListView):
    """Listado de marcas."""

    model = Brand
    template_name = "catalog/brand_list.html"
    context_object_name = "brands"

    def get_queryset(self):
        """Usa el selector ``active_brands``."""
        return selectors.active_brands()


class BrandCreateView(CreateView):
    """Alta de marca."""

    model = Brand
    form_class = BrandForm
    template_name = "catalog/brand_form.html"
    success_url = reverse_lazy("catalog:brand-list")


class BrandUpdateView(UpdateView):
    """Edicion de marca."""

    model = Brand
    form_class = BrandForm
    template_name = "catalog/brand_form.html"
    success_url = reverse_lazy("catalog:brand-list")


class UnitListView(_BaseCatalogListView):
    """Listado de unidades de medida."""

    model = UnitOfMeasure
    template_name = "catalog/unit_list.html"
    context_object_name = "units"

    def get_queryset(self):
        """Usa el selector ``active_units``."""
        return selectors.active_units()


class UnitCreateView(CreateView):
    """Alta de unidad de medida."""

    model = UnitOfMeasure
    form_class = UnitForm
    template_name = "catalog/unit_form.html"
    success_url = reverse_lazy("catalog:unit-list")


class UnitUpdateView(UpdateView):
    """Edicion de unidad de medida."""

    model = UnitOfMeasure
    form_class = UnitForm
    template_name = "catalog/unit_form.html"
    success_url = reverse_lazy("catalog:unit-list")


class ProductListView(_BaseCatalogListView):
    """Listado de productos con busqueda."""

    model = Product
    template_name = "catalog/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        """Aplica filtro de busqueda por ``term``."""
        term = self.request.GET.get("q", "").strip()
        qs = selectors.active_products()
        if term:
            qs = selectors.search_products(term)
        return qs

    def get_context_data(self, **kwargs):
        """Inyecta el termino de busqueda en el contexto."""
        context = super().get_context_data(**kwargs)
        context["term"] = self.request.GET.get("q", "")
        return context


class ProductCreateView(CreateView):
    """Alta de producto."""

    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog:product-list")

    def form_valid(self, form):
        """Llama al service."""
        self.object = services.create_product(  # pylint: disable=attribute-defined-outside-init
            user=self.request.user, **form.cleaned_data
        )
        messages.success(self.request, f"Producto '{self.object.sku}' creado.")
        return HttpResponseRedirect(self.get_success_url())


class ProductUpdateView(UpdateView):
    """Edicion de producto."""

    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog:product-list")

    def form_valid(self, form):
        """Llama al service."""
        services.update_product(
            self.object, user=self.request.user, **form.cleaned_data
        )
        messages.success(
            self.request, f"Producto '{self.object.sku}' actualizado."
        )
        return HttpResponseRedirect(self.get_success_url())


class ProductDeactivateView(DeleteView):
    """Desactivacion logica de producto."""

    model = Product
    template_name = "catalog/product_confirm_delete.html"
    success_url = reverse_lazy("catalog:product-list")

    def form_valid(self, form):
        """Sobrescribe ``DeleteView`` para desactivar en lugar de borrar."""
        services.deactivate_product(self.get_object(), user=self.request.user)
        messages.success(
            self.request, f"Producto '{self.get_object().sku}' desactivado."
        )
        return HttpResponseRedirect(self.get_success_url())


__all__ = [
    "CategoryListView",
    "CategoryCreateView",
    "CategoryUpdateView",
    "BrandListView",
    "BrandCreateView",
    "BrandUpdateView",
    "UnitListView",
    "UnitCreateView",
    "UnitUpdateView",
    "ProductListView",
    "ProductCreateView",
    "ProductUpdateView",
    "ProductDeactivateView",
]
