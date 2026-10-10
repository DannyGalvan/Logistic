"""Registro de modelos del nucleo en el admin de Django."""

from __future__ import annotations

from django.contrib import admin

from .models import DocumentSequence


@admin.register(DocumentSequence)
class DocumentSequenceAdmin(admin.ModelAdmin):
    """Admin de solo lectura para ``DocumentSequence``."""

    list_display = ("prefix", "last_number")
    readonly_fields = ("last_number",)

    def has_add_permission(self, request) -> bool:
        """No permite agregar manualmente; se crean por codigo."""
        return False
