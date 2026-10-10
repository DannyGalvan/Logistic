"""Filtros y tags de plantilla para formato visual."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django import template
from django.urls import Resolver404, resolve

register = template.Library()


@register.filter(name="money")
def money(value: object) -> str:
    """Formatea un valor monetario con dos cifras decimales."""
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


@register.filter(name="status_soft")
def status_soft(value: str) -> str:
    """Devuelve la clase ``badge-soft-*`` segun el estado."""
    palette: dict[str, str] = {
        "DRAFT": "badge-soft-secondary",
        "CONFIRMED": "badge-soft-primary",
        "PARTIALLY_RECEIVED": "badge-soft-warning",
        "RECEIVED": "badge-soft-success",
        "PARTIALLY_SHIPPED": "badge-soft-warning",
        "SHIPPED": "badge-soft-success",
        "CANCELLED": "badge-soft-danger",
        "IN_PROGRESS": "badge-soft-info",
        "APPROVED": "badge-soft-success",
        "SUCCESS": "badge-soft-success",
        "FAILED": "badge-soft-danger",
    }
    return palette.get(value, "badge-soft-secondary")


@register.simple_tag(name="nav_active", takes_context=True)
def nav_active(context, url_name: str) -> str:
    """Devuelve ``active`` si la URL coincide con la ruta actual."""
    request = context.get("request")
    if request is None:
        return ""
    try:
        match = resolve(request.path)
    except Resolver404:
        return ""
    current = (
        f"{match.namespace}:{match.url_name}" if match.namespace else match.url_name
    )
    return "active" if current == url_name else ""
