"""Senales (Observer) del modulo de inventario."""

from __future__ import annotations

from django.dispatch import Signal, receiver

from .services import AlertService


# Senal que dispara el ``AlertService`` cuando cambia el stock.
stock_changed = Signal()


@receiver(stock_changed)
def evaluate_product(sender, **kwargs):  # type: ignore[no-untyped-def]
    """Evalua alertas tras un cambio de stock."""
    product = kwargs.get("product")
    if product is None:
        return
    AlertService().evaluate_product(product)


__all__ = ["stock_changed"]
