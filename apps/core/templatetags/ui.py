"""Filtros y tags de plantilla para formato visual."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter(name="money")
def money(value: object) -> str:
    """Formatea un valor monetario con dos cifras decimales.

    Args:
        value: ``Decimal``, ``int``, ``float`` o ``str`` convertible.

    Returns:
        Cadena formateada con separador de miles y dos decimales, o
        ``"-"`` si el valor no es convertible.
    """
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return "-"
    quantized = amount.quantize(Decimal("0.01"))
    return f"Q{quantized:,.2f}"


@register.filter(name="qty")
def qty(value: object) -> str:
    """Formatea una cantidad con tres decimales."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return "-"
    quantized = amount.quantize(Decimal("0.001"))
    return f"{quantized:,.3f}"


@register.filter(name="status_badge")
def status_badge(value: str) -> str:
    """Devuelve la clase CSS del badge segun el estado."""
    palette: dict[str, str] = {
        "DRAFT": "bg-secondary",
        "CONFIRMED": "bg-primary",
        "PARTIALLY_RECEIVED": "bg-warning text-dark",
        "RECEIVED": "bg-success",
        "PARTIALLY_SHIPPED": "bg-warning text-dark",
        "SHIPPED": "bg-success",
        "CANCELLED": "bg-danger",
        "IN_PROGRESS": "bg-info text-dark",
        "APPROVED": "bg-success",
    }
    return palette.get(value, "bg-secondary")
