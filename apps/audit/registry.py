"""Registro de modelos auditables (Observer)."""

from __future__ import annotations

from typing import Iterable

from django.apps import apps


AUDITED_MODELS: set[str] = set()
_excluded: dict[str, set[str]] = {}


def register(
    model_label: str,
    exclude_fields: Iterable[str] = (),
) -> None:
    """Registra un modelo para auditoria.

    Args:
        model_label: ``app_label.ModelName`` (ej. ``catalog.Product``).
        exclude_fields: Campos a excluir del diff (ej. ``updated_at``).
    """
    AUDITED_MODELS.add(model_label)
    _excluded[model_label] = set(exclude_fields)


def is_audited(model_label: str) -> bool:
    """Indica si un modelo esta auditado."""
    return model_label in AUDITED_MODELS


def get_excluded(model_label: str) -> set[str]:
    """Devuelve el set de campos excluidos."""
    return _excluded.get(model_label, set())


def resolve_model(model_label: str):
    """Resuelve la clase de modelo desde su label textual."""
    return apps.get_model(model_label)


__all__ = ["register", "is_audited", "get_excluded", "resolve_model"]
