"""Servicios de la app ``audit``."""

from __future__ import annotations

from typing import Any

from django.contrib.contenttypes.models import ContentType

from .models import AuditLog


def log(
    *,
    user: Any,
    action: str,
    obj: Any = None,
    changes: dict | None = None,
    ip_address: str | None = None,
    object_repr: str = "",
) -> AuditLog:
    """Registra una entrada en la bitacora."""
    payload: dict[str, Any] = {
        "user": user if (user is not None and user.is_authenticated) else None,
        "action": action,
        "ip_address": ip_address,
        "changes": changes or {},
        "object_repr": object_repr[:200],
    }
    if obj is not None:
        payload["object_repr"] = str(obj)[:200]
        payload["content_type"] = ContentType.objects.get_for_model(
            obj.__class__
        )
        payload["object_id"] = str(obj.pk) if obj.pk is not None else ""
    return AuditLog.objects.create(**payload)


def log_login_success(user: Any, ip_address: str | None) -> AuditLog:
    """Registra login exitoso."""
    return log(user=user, action="LOGIN", ip_address=ip_address,
               object_repr=str(user))


def log_logout(user: Any, ip_address: str | None) -> AuditLog:
    """Registra logout."""
    return log(user=user, action="LOGOUT", ip_address=ip_address,
               object_repr=str(user) if user else "")


def log_login_failed(username: str, ip_address: str | None) -> AuditLog:
    """Registra intento de login fallido (sin objeto asociado)."""
    return log(user=None, action="LOGIN_FAILED", ip_address=ip_address,
               object_repr=username)


__all__ = [
    "log",
    "log_login_success",
    "log_logout",
    "log_login_failed",
]
