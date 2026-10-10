"""Modelos de la app ``purchasing``.

Cuatro entidades: ``PurchaseOrder`` (OC), ``PurchaseOrderLine``,
``GoodsReceipt`` (REC) y ``GoodsReceiptLine``. ``PurchaseOrder``
hereda de ``UserStampedModel``.
"""

from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import UserStampedModel


class PurchaseOrder(UserStampedModel):
    """Orden de compra."""

    class Status(models.TextChoices):
        """Estado de la orden."""

        DRAFT = "DRAFT", "Borrador"
        CONFIRMED = "CONFIRMED", "Confirmada"
        PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED", "Recibida parcial"
        RECEIVED = "RECEIVED", "Recibida"
        CANCELLED = "CANCELLED", "Cancelada"

    code = models.CharField(max_length=20, unique=True)
    supplier = models.ForeignKey(
        "partners.Supplier", on_delete=models.PROTECT, related_name="orders"
    )
    warehouse = models.ForeignKey(
        "warehouses.Warehouse", on_delete=models.PROTECT, related_name="orders"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    order_date = models.DateField()
    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Orden de compra"
        verbose_name_plural = "Ordenes de compra"
        ordering = ["-code"]

    def __str__(self) -> str:
        """Devuelve ``code - supplier``."""
        return f"{self.code} - {self.supplier.name}"

    @property
    def total(self) -> Decimal:
        """Suma los subtotales de las lineas."""
        return sum((line.subtotal for line in self.lines.all()), Decimal("0"))

    @property
    def is_editable(self) -> bool:
        """Indica si la orden es editable (solo DRAFT)."""
        return self.status == self.Status.DRAFT


class PurchaseOrderLine(models.Model):
    """Linea de una orden de compra."""

    order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name="lines"
    )
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.PROTECT, related_name="+"
    )
    quantity = models.DecimalField(
        max_digits=14, decimal_places=3, validators=[MinValueValidator(0)]
    )
    unit_cost = models.DecimalField(
        max_digits=14, decimal_places=4, default=Decimal("0")
    )
    received_quantity = models.DecimalField(
        max_digits=14, decimal_places=3, default=Decimal("0")
    )

    class Meta:
        verbose_name = "Linea de orden"
        verbose_name_plural = "Lineas de orden"

    @property
    def pending_quantity(self) -> Decimal:
        """Cantidad pendiente de recibir."""
        return self.quantity - self.received_quantity

    @property
    def subtotal(self) -> Decimal:
        """Subtotal de la linea."""
        return self.quantity * self.unit_cost


class GoodsReceipt(UserStampedModel):
    """Recepcion de mercancia."""

    code = models.CharField(max_length=20, unique=True)
    order = models.ForeignKey(
        PurchaseOrder, on_delete=models.PROTECT, related_name="receipts"
    )
    location = models.ForeignKey(
        "warehouses.Location", on_delete=models.PROTECT, related_name="receipts"
    )
    received_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Recepcion"
        verbose_name_plural = "Recepciones"
        ordering = ["-code"]


class GoodsReceiptLine(models.Model):
    """Linea de una recepcion."""

    receipt = models.ForeignKey(
        GoodsReceipt, on_delete=models.CASCADE, related_name="lines"
    )
    order_line = models.ForeignKey(
        PurchaseOrderLine, on_delete=models.PROTECT, related_name="receipt_lines"
    )
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    lot_number = models.CharField(max_length=40, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    movement = models.OneToOneField(
        "inventory.StockMovement",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )


__all__ = [
    "PurchaseOrder",
    "PurchaseOrderLine",
    "GoodsReceipt",
    "GoodsReceiptLine",
]
