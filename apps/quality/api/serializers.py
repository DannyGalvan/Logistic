"""Serializers de ``quality``."""

from __future__ import annotations

from rest_framework import serializers

from ..models import LintMessageRecord, LintRun


class LintMessageSerializer(serializers.ModelSerializer):
    """Mensaje de Pylint de una corrida."""

    class Meta:
        model = LintMessageRecord
        fields = ["id", "type", "message_id", "symbol", "message_text", "module",
                  "obj", "path", "line", "column"]


class LintRunSerializer(serializers.ModelSerializer):
    """Corrida de Pylint."""

    class Meta:
        model = LintRun
        fields = ["id", "target", "status", "score", "convention_count",
                  "refactor_count", "warning_count", "error_count", "fatal_count",
                  "info_count", "modules_linted", "duration_ms", "triggered_by",
                  "source", "error_detail", "created_at"]


class LintRunDetailSerializer(LintRunSerializer):
    """Corrida con sus mensajes."""

    messages = LintMessageSerializer(many=True, read_only=True)

    class Meta(LintRunSerializer.Meta):
        fields = [*LintRunSerializer.Meta.fields, "messages"]


class RunInputSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Objetivos opcionales de la corrida (default ``PYLINT_TARGETS``)."""

    targets = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
