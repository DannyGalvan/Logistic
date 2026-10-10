"""Receivers (Observer) del modulo de inventario."""

from __future__ import annotations

from django.dispatch import receiver

from .events import stock_changed
from .services import AlertService


@receiver(stock_changed)
def evaluate_product(sender, **kwargs):  # type: ignore[no-untyped-def]  # pylint: disable=unused-argument
    """Evalua alertas de stock bajo tras un movimiento."""
    product = kwargs.get("product")
    if product is None:
        return
    AlertService().evaluate_product(product)


__all__ = ["stock_changed", "evaluate_product"]
