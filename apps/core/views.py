"""Vistas base, mixins y manejadores de errores del nucleo."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic import View
from django_filters.views import FilterView

from .selectors import dashboard_context


class HtmxTemplateMixin:
    """Resuelve una plantilla parcial cuando la peticion viene de HTMX.

    Atributos:
        partial_template_name (str|None): Plantilla a usar bajo HTMX.
    """

    partial_template_name: str | None = None

    def get_template_names(self) -> list[str]:
        """Devuelve el nombre de plantilla adecuado segun el origen."""
        names = super().get_template_names()  # type: ignore[misc]
        request: HttpRequest = self.request  # type: ignore[attr-defined]
        if (
            self.partial_template_name
            and getattr(request, "htmx", False)
            and self.partial_template_name not in names
        ):
            names.append(self.partial_template_name)
        return names


class BaseListView(
    LoginRequiredMixin, PermissionRequiredMixin, HtmxTemplateMixin, FilterView
):
    """ListView base con paginacion, filtros y permisos."""

    paginate_by = 20
    raise_exception = True

    def get_base_queryset(self) -> Any:
        """Hook que las subclases usan para devolver el queryset."""
        raise ImproperlyConfigured(
            f"{type(self).__name__} debe implementar get_base_queryset()."
        )

    def get_queryset(self) -> Any:
        """Devuelve el queryset del modelo a partir del hook."""
        return self.get_base_queryset()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Inyecta banderas de HTMX y filtros en el contexto."""
        context = super().get_context_data(**kwargs)
        context["is_htmx"] = getattr(self.request, "htmx", False)
        return context


class BaseDashboardView(LoginRequiredMixin, View):
    """Vista de dashboard por defecto para la portada."""

    template_name = "core/dashboard.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Renderiza el dashboard con KPIs y actividad reciente."""
        return render(request, self.template_name, dashboard_context())


def error_403(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    """Renderiza la plantilla de error 403."""
    _ = exception  # Django pasa la excepcion; la ignoramos
    return render(request, "errors/403.html", status=403)


def error_404(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    """Renderiza la plantilla de error 404."""
    _ = exception  # Django pasa la excepcion; la ignoramos
    return render(request, "errors/404.html", status=404)


def error_500(request: HttpRequest) -> HttpResponse:
    """Renderiza la plantilla de error 500."""
    return render(request, "errors/500.html", status=500)
