"""Admin de Django para ``audit``."""

from __future__ import annotations

from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin de solo lectura para ``AuditLog``."""

    list_display = ("timestamp", "user", "action", "object_repr")
    list_filter = ("action",)
    search_fields = ("object_repr", "user__username")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request) -> bool:
        """No permite agregar manualmente."""
        return False
