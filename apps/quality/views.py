"""Vistas web del modulo ``/calidad/``."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import ListView, TemplateView, View

from apps.core.views import LoginRequiredMixin, PermissionRequiredMixin

from . import services
from .catalog import MessageCatalog
from .demo_snippets import DEMO_SNIPPETS
from .models import LintRun

CATEGORY_LABELS: tuple[tuple[str, str], ...] = (
    ("C", "Convencion"),
    ("R", "Refactor"),
    ("W", "Advertencia"),
    ("E", "Error"),
    ("F", "Fatal"),
    ("I", "Informativo"),
)


def _load_demo(key: str) -> str:
    """Devuelve el codigo fuente de un snippet demo o cadena vacia."""
    demo = DEMO_SNIPPETS.get(key)
    if demo is None:
        return ""
    path = Path(settings.BASE_DIR) / demo["path"]
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


class QualityDashboardView(
    LoginRequiredMixin, PermissionRequiredMixin, TemplateView,
):
    """Dashboard principal con la ultima corrida."""

    permission_required = "quality.view_lintrun"
    template_name = "quality/dashboard.html"

    def get_context_data(self, **kwargs):  # type: ignore[no-untyped-def]
        """Inyecta la ultima corrida y la serie."""
        context = super().get_context_data(**kwargs)
        context["last_run"] = LintRun.objects.order_by("-created_at").first()
        context["recent_runs"] = list(
            LintRun.objects.order_by("-created_at")[:20]
        )
        return context

    def post(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        """Ejecuta Pylint via POST."""
        try:
            run = services.LintService().run_project(
                targets=None,
                user=request.user,
                source="WEB",
            )
            messages.success(request, f"Corrida {run.pk} completada.")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            messages.error(request, f"Error: {exc}")
        return HttpResponseRedirect(reverse("quality:dashboard"))


class LintRunListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Historial de corridas."""

    permission_required = "quality.view_lintrun"
    template_name = "quality/run_list.html"
    context_object_name = "runs"
    paginate_by = 30
    queryset = LintRun.objects.order_by("-created_at")


class LintRunDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, View,
):
    """Detalle de una corrida con la tabla de mensajes."""

    permission_required = "quality.view_lintrun"

    def get(self, request, pk: int) -> HttpResponse:
        """Renderiza la tabla de mensajes."""
        run = get_object_or_404(LintRun, pk=pk)
        messages_qs = run.messages.all().order_by("path", "line")
        return render(
            request,
            "quality/run_detail.html",
            {"run": run, "lint_messages": messages_qs},
        )


class SnippetAnalyzeView(
    LoginRequiredMixin, PermissionRequiredMixin, View,
):
    """Analiza un snippet de codigo."""

    permission_required = "quality.view_lintrun"

    def post(self, request) -> HttpResponse:
        """Procesa el POST con el codigo."""
        code = request.POST.get("code", "")
        try:
            result, _ = services.LintService().analyze_snippet(code=code)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            messages.error(request, f"Error: {exc}")
            result = None
        return render(
            request,
            "quality/snippet.html",
            {"code": code, "result": result, "demos": DEMO_SNIPPETS},
        )

    def get(self, request) -> HttpResponse:
        """Muestra el formulario, opcionalmente precargado con un demo."""
        code = _load_demo(request.GET.get("demo", ""))
        return render(
            request,
            "quality/snippet.html",
            {"code": code, "result": None, "demos": DEMO_SNIPPETS},
        )


class CatalogView(
    LoginRequiredMixin, PermissionRequiredMixin, TemplateView,
):
    """Buscador del catalogo de mensajes."""

    permission_required = "quality.view_lintrun"
    template_name = "quality/catalog.html"

    def get_context_data(self, **kwargs):  # type: ignore[no-untyped-def]
        """Filtra el catalogo segun ``q`` o ``cat``."""
        context = super().get_context_data(**kwargs)
        catalog = MessageCatalog()
        term = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("cat", "").strip().upper()
        if term:
            context["entries"] = catalog.search(term)
        elif category:
            context["entries"] = catalog.by_category(category)
        else:
            context["entries"] = catalog.entries
        context["term"] = term
        context["category"] = category
        context["categories"] = CATEGORY_LABELS
        return context


class RunPylintView(
    LoginRequiredMixin, PermissionRequiredMixin, View,
):
    """Ejecuta Pylint via POST (accion explicita)."""

    permission_required = "quality.run_lint"

    def post(self, request) -> HttpResponse:
        """Lanza Pylint y redirige al dashboard."""
        try:
            services.LintService().run_project(user=request.user, source="WEB")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            messages.error(request, f"Error: {exc}")
        return HttpResponseRedirect(reverse("quality:dashboard"))


__all__ = [
    "QualityDashboardView",
    "LintRunListView",
    "LintRunDetailView",
    "SnippetAnalyzeView",
    "CatalogView",
    "RunPylintView",
]
