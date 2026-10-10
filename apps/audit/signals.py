"""Senales para registrar eventos de auditoria."""

from __future__ import annotations

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
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


def _client_ip(request) -> str | None:  # type: ignore[no-untyped-def]
    """IP del cliente (``REMOTE_ADDR``) o ``None``."""
    if request is None:
        return None
    return request.META.get("REMOTE_ADDR") or None


@receiver(user_logged_in)
def record_login(sender, request, user, **kwargs):  # type: ignore[no-untyped-def]  # pylint: disable=unused-argument
    """Registra ``LOGIN``."""
    services.log_login_success(user, _client_ip(request))


@receiver(user_logged_out)
def record_logout(sender, request, user, **kwargs):  # type: ignore[no-untyped-def]  # pylint: disable=unused-argument
    """Registra ``LOGOUT``."""
    services.log_logout(user, _client_ip(request))


@receiver(user_login_failed)
def record_login_failed(sender, credentials, request=None, **kwargs):  # type: ignore[no-untyped-def]  # pylint: disable=unused-argument
    """Registra ``LOGIN_FAILED`` con el usuario intentado."""
    services.log_login_failed(credentials.get("username", ""), _client_ip(request))


__all__ = ["AUDITED_MODELS", "resolve_model"]
