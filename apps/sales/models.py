"""Modelos de la app ``sales``.

Cuatro entidades: ``SalesOrder`` (OV), ``SalesOrderLine``, ``Shipment``
(DES) y ``ShipmentLine``.
"""

from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from apps.core.models import UserStampedModel


class SalesOrder(UserStampedModel):
    """Orden de venta."""

    class Status(models.TextChoices):
        """Estado de la orden."""

        DRAFT = "DRAFT", "Borrador"
        CONFIRMED = "CONFIRMED", "Confirmada"
        PARTIALLY_SHIPPED = "PARTIALLY_SHIPPED", "Despachada parcial"
        SHIPPED = "SHIPPED", "Despachada"
        CANCELLED = "CANCELLED", "Cancelada"

    code = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(
        "partners.Customer", on_delete=models.PROTECT, related_name="orders"
    )
    warehouse = models.ForeignKey(
        "warehouses.Warehouse", on_delete=models.PROTECT, related_name="sales_orders"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    order_date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Orden de venta"
        verbose_name_plural = "Ordenes de venta"
        ordering = ["-code"]

    def __str__(self) -> str:
        """Devuelve ``code - customer``."""
        return f"{self.code} - {self.customer.name}"

    def get_absolute_url(self) -> str:
        """URL del detalle de la orden."""
        return reverse("sales:order-detail", args=[self.pk])

    @property
    def total(self) -> Decimal:
        """Suma los subtotales."""
        return sum((line.subtotal for line in self.lines.all()), Decimal("0"))

    @property
    def is_editable(self) -> bool:
        """Indica si la orden es editable (solo DRAFT)."""
        return self.status == self.Status.DRAFT


class SalesOrderLine(models.Model):
    """Linea de una orden de venta."""

    order = models.ForeignKey(
        SalesOrder, on_delete=models.CASCADE, related_name="lines"
    )
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.PROTECT, related_name="+"
    )
    quantity = models.DecimalField(
        max_digits=14, decimal_places=3, validators=[MinValueValidator(0)]
    )
    unit_price = models.DecimalField(
        max_digits=14, decimal_places=4, default=Decimal("0")
    )
    shipped_quantity = models.DecimalField(
        max_digits=14, decimal_places=3, default=Decimal("0")
    )

    class Meta:
        verbose_name = "Linea de venta"
        verbose_name_plural = "Lineas de venta"

    @property
    def pending_quantity(self) -> Decimal:
        """Cantidad pendiente de despachar."""
        return self.quantity - self.shipped_quantity

    @property
    def subtotal(self) -> Decimal:
        """Subtotal de la linea."""
        return self.quantity * self.unit_price


class Shipment(UserStampedModel):
    """Despacho de mercancia."""

    code = models.CharField(max_length=20, unique=True)
    order = models.ForeignKey(
        SalesOrder, on_delete=models.PROTECT, related_name="shipments"
    )
    shipped_at = models.DateTimeField(auto_now_add=True)
    carrier = models.CharField(max_length=80, blank=True)
    tracking_number = models.CharField(max_length=80, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Despacho"
        verbose_name_plural = "Despachos"
        ordering = ["-code"]


class ShipmentLine(models.Model):
    """Linea de despacho."""

    shipment = models.ForeignKey(
        Shipment, on_delete=models.CASCADE, related_name="lines"
    )
    order_line = models.ForeignKey(
        SalesOrderLine, on_delete=models.PROTECT, related_name="shipment_lines"
    )
    location = models.ForeignKey(
        "warehouses.Location", on_delete=models.PROTECT, related_name="+"
    )
    lot = models.ForeignKey(
        "inventory.Lot", on_delete=models.PROTECT, null=True, blank=True,
        related_name="+",
    )
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    movement = models.OneToOneField(
        "inventory.StockMovement",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )


__all__ = [
    "SalesOrder",
    "SalesOrderLine",
    "Shipment",
    "ShipmentLine",
]
