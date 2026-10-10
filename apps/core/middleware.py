"""Middlewares personalizados del nucleo."""

from __future__ import annotations

import contextvars
from typing import Optional

_current_user: contextvars.ContextVar[object] = contextvars.ContextVar(
    "current_user", default=None,
)


def get_current_user() -> Optional[object]:
    """Devuelve el usuario asociado al request actual.

    Returns:
        Instancia de ``AUTH_USER_MODEL`` o ``None`` si no hay.
    """
    return _current_user.get()


class CurrentUserMiddleware:
    """Almacena el usuario autenticado en una ``ContextVar``.

    El modulo ``audit`` lo consulta para registrar el autor de cada
    cambio sin acoplar ``AuditLog`` a la ``request`` global.
    """

    def __init__(self, get_response):
        """Inicializa el middleware con la funcion ``get_response``."""
        self.get_response = get_response

    def __call__(self, request):
        """Procesa la request almacenando ``request.user``."""
        token = _current_user.set(getattr(request, "user", None))
        try:
            return self.get_response(request)
        finally:
            _current_user.reset(token)
