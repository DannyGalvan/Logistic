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
) -> AuditLog:
    """Registra una entrada en la bitacora."""
    payload: dict[str, Any] = {
        "user": user if (user is not None and user.is_authenticated) else None,
        "action": action,
        "ip_address": ip_address,
        "changes": changes or {},
    }
    if obj is not None:
        payload["object_repr"] = str(obj)[:200]
        payload["content_type"] = ContentType.objects.get_for_model(
            obj.__class__
        )
        try:
            payload["object_id"] = str(obj.pk)
        except Exception:  # pylint: disable=broad-exception-caught
            payload["object_id"] = ""
    return AuditLog.objects.create(**payload)


def log_login_success(user: Any, ip_address: str | None) -> AuditLog:
    """Registra login exitoso."""
    return log(user=user, action="LOGIN", ip_address=ip_address)


def log_logout(user: Any, ip_address: str | None) -> AuditLog:
    """Registra logout."""
    return log(user=user, action="LOGOUT", ip_address=ip_address)


def log_login_failed(username: str, ip_address: str | None) -> AuditLog:
    """Registra intento de login fallido."""
    return log(
        user=None,
        action="LOGIN_FAILED",
        obj=type("Anon", (), {"__str__": lambda self: username})(),
        ip_address=ip_address,
    )


__all__ = [
    "log",
    "log_login_success",
    "log_logout",
    "log_login_failed",
]
