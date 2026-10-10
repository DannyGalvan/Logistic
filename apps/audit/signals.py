"""Senales para registrar eventos de auditoria."""

from __future__ import annotations

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.core.middleware import get_current_user

from . import services
from .registry import (
    AUDITED_MODELS,
    get_excluded,
    is_audited,
    resolve_model,
)


_pre_save_state: dict[int, dict] = {}


def _model_label(instance) -> str:
    """Devuelve ``app_label.ModelName`` para ``instance``."""
    return instance._meta.label_lower


@receiver(pre_save)
def capture_pre_save(sender, instance, **kwargs):  # type: ignore[no-untyped-def]
    """Captura el estado previo del modelo para calcular el diff."""
    label = _model_label(instance)
    if not is_audited(label):
        return
    try:
        previous = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        _pre_save_state[id(instance)] = {}
        return
    excluded = get_excluded(label)
    diff = {}
    for field in sender._meta.fields:
        if field.name in excluded:
            continue
        old = getattr(previous, field.name)
        new = getattr(instance, field.name)
        if old != new:
            diff[field.name] = [str(old), str(new)]
    _pre_save_state[id(instance)] = diff


@receiver(post_save)
def record_post_save(sender, instance, created, **kwargs):  # type: ignore[no-untyped-def]
    """Registra ``CREATE`` o ``UPDATE``."""
    label = _model_label(instance)
    if not is_audited(label):
        return
    user = get_current_user()
    if created:
        services.log(user=user, action="CREATE", obj=instance)
    else:
        diff = _pre_save_state.pop(id(instance), {})
        if diff:
            services.log(user=user, action="UPDATE", obj=instance, changes=diff)


@receiver(post_delete)
def record_post_delete(sender, instance, **kwargs):  # type: ignore[no-untyped-def]
    """Registra ``DELETE``."""
    label = _model_label(instance)
    if not is_audited(label):
        return
    user = get_current_user()
    services.log(user=user, action="DELETE", obj=instance)


__all__ = ["AUDITED_MODELS", "resolve_model"]
