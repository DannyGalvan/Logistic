"""Vistas base, mixins y manejadores de errores del nucleo."""

from __future__ import annotations

import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.generic import View
from django_filters.views import FilterView

from .exceptions import DomainError
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


def error_text(exc: Exception) -> str:
    """Devuelve un texto legible para errores de dominio o validacion."""
    if isinstance(exc, ValidationError):
        return " ".join(exc.messages)
    return str(exc)


def parse_decimal(raw: str | None) -> Decimal | None:
    """Convierte texto a ``Decimal`` o ``None`` si esta vacio o es invalido."""
    try:
        return Decimal(raw) if raw else None
    except InvalidOperation:
        return None


def parse_date(raw: str | None) -> datetime.date | None:
    """Convierte ``YYYY-MM-DD`` a ``date`` o ``None`` si es invalido."""
    try:
        return datetime.date.fromisoformat(raw) if raw else None
    except ValueError:
        return None


def form_errors_text(form: Any) -> str:
    """Aplana los errores de un formulario en un unico texto."""
    return " ".join(
        f"{field}: {' '.join(errors)}" for field, errors in form.errors.items()
    )


class ServiceActionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Vista POST que ejecuta una accion de service sobre un objeto.

    Las subclases definen ``model``, ``permission_required``,
    ``success_message`` y ``perform``. Los errores de dominio o de
    validacion se muestran como mensaje y no generan un 500.
    """

    model: Any = None
    success_message: str = "Operacion registrada."
    http_method_names = ["post"]
    raise_exception = True

    def perform(self, obj: Any, request: HttpRequest) -> None:
        """Ejecuta la accion; las subclases deben implementarla."""
        raise ImproperlyConfigured(
            f"{type(self).__name__} debe implementar perform()."
        )

    def get_redirect_url(self, obj: Any) -> str:
        """URL de retorno tras la accion (por defecto el detalle)."""
        return obj.get_absolute_url()

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Busca el objeto, ejecuta la accion y redirige."""
        obj = get_object_or_404(self.model, pk=pk)
        try:
            self.perform(obj, request)
        except (DomainError, ValidationError) as exc:
            messages.error(request, error_text(exc))
        else:
            messages.success(request, self.success_message)
        return HttpResponseRedirect(self.get_redirect_url(obj))


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
