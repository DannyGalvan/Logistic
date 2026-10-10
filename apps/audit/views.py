"""Vistas de la app ``audit``."""

from __future__ import annotations

from django.views.generic import ListView

from apps.core.views import LoginRequiredMixin, PermissionRequiredMixin

from .models import AuditLog


class AuditListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Listado de la bitacora."""

    permission_required = "audit.view_auditlog"
    template_name = "audit/audit_list.html"
    context_object_name = "logs"
    paginate_by = 50
    queryset = AuditLog.objects.select_related(
        "user", "content_type"
    ).order_by("-timestamp")


__all__ = ["AuditListView"]
