"""Modelos de la app ``quality``.

``LintRun`` y ``LintMessageRecord`` persisten las corridas de Pylint
para el modulo web ``/calidad/``.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


class LintRun(models.Model):
    """Una corrida de Pylint sobre el proyecto."""

    class Status(models.TextChoices):
        """Estado de la corrida."""

        SUCCESS = "SUCCESS", "Exitoso"
        FAILED = "FAILED", "Fallido"

    class Source(models.TextChoices):
        """Origen de la corrida."""

        WEB = "WEB", "Web"
        CLI = "CLI", "CLI"
        SNIPPET = "SNIPPET", "Snippet"

    target = models.CharField(max_length=200)
    status = models.CharField(
        max_length=8, choices=Status.choices, default=Status.SUCCESS
    )
    score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
    )
    convention_count = models.PositiveIntegerField(default=0)
    refactor_count = models.PositiveIntegerField(default=0)
    warning_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    fatal_count = models.PositiveIntegerField(default=0)
    info_count = models.PositiveIntegerField(default=0)
    modules_linted = models.PositiveIntegerField(default=0)
    duration_ms = models.PositiveIntegerField(default=0)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    source = models.CharField(
        max_length=8, choices=Source.choices, default=Source.WEB
    )
    error_detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Corrida de Pylint"
        verbose_name_plural = "Corridas de Pylint"
        ordering = ["-created_at"]


class LintMessageRecord(models.Model):
    """Un mensaje emitido por Pylint en una corrida."""

    run = models.ForeignKey(
        LintRun, on_delete=models.CASCADE, related_name="messages"
    )
    type = models.CharField(max_length=12)
    message_id = models.CharField(max_length=12)
    symbol = models.CharField(max_length=64)
    message_text = models.TextField()
    module = models.CharField(max_length=200, blank=True)
    obj = models.CharField(max_length=200, blank=True)
    path = models.CharField(max_length=300, blank=True)
    line = models.PositiveIntegerField(default=0)
    column = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Mensaje de Pylint"
        verbose_name_plural = "Mensajes de Pylint"
        indexes = [
            models.Index(fields=["run", "message_id"]),
        ]


__all__ = ["LintRun", "LintMessageRecord"]
