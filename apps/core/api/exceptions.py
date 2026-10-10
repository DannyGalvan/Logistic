"""Manejador de excepciones DRF que mapea ``DomainError`` a HTTP 400."""

from __future__ import annotations

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from ..exceptions import DomainError


def domain_exception_handler(exc, context):  # type: ignore[no-untyped-def]
    """Devuelve una respuesta 400 cuando ``exc`` es ``DomainError``.

    Args:
        exc: Excepcion capturada por DRF.
        context: Contexto de la vista proporcionado por DRF.

    Returns:
        ``Response`` 400 si la excepcion es de dominio; en otro caso
        delega al manejador por defecto de DRF.
    """
    if isinstance(exc, DomainError):
        payload = {"detail": exc.message or str(exc), "code": exc.__class__.__name__}
        return Response(payload, status=400)
    return drf_exception_handler(exc, context)
