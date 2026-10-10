"""Admin de ``quality``."""

from __future__ import annotations

from django.contrib import admin

from .models import LintMessageRecord, LintRun


class LintMessageInline(admin.TabularInline):
    """Inline de mensajes en la corrida."""

    model = LintMessageRecord
    extra = 0
    fields = ("message_id", "path", "line", "column", "message_text")


@admin.register(LintRun)
class LintRunAdmin(admin.ModelAdmin):
    """Admin de corridas."""

    list_display = (
        "created_at", "target", "score", "status", "duration_ms",
        "source",
    )
    list_filter = ("status", "source")
    inlines = [LintMessageInline]


@admin.register(LintMessageRecord)
class LintMessageRecordAdmin(admin.ModelAdmin):
    """Admin de mensajes."""

    list_display = ("run", "message_id", "path", "line")
