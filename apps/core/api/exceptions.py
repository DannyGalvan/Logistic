"""Manejador de excepciones DRF que mapea errores de dominio a HTTP 400."""

from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from ..exceptions import DomainError


def domain_exception_handler(exc, context):  # type: ignore[no-untyped-def]
    """Devuelve una respuesta 400 para ``DomainError`` y ``ValidationError``.

    Args:
        exc: Excepcion capturada por DRF.
        context: Contexto de la vista proporcionado por DRF.

    Returns:
        ``Response`` 400 si la excepcion es de dominio o de validacion de
        Django (lanzada por los services); en otro caso delega al
        manejador por defecto de DRF.
    """
    if isinstance(exc, DomainError):
        payload = {"detail": exc.message or str(exc), "code": exc.__class__.__name__}
        return Response(payload, status=400)
    if isinstance(exc, DjangoValidationError):
        return Response(
            {"detail": " ".join(exc.messages), "code": "ValidationError"},
            status=400,
        )
    return drf_exception_handler(exc, context)
