"""Modelos de la app ``inventory``.

``Lot``: lote de un producto (con caducidad opcional).
``Stock``: existencia por ``(producto, ubicacion, lote)``.
``StockMovement``: movimiento inmutable que registra entradas y
salidas (receipt, issue, transfer, adjustment).
``CycleCount`` y ``CycleCountLine``: conteos ciclicos con
aprobacion. ``Alert``: avisos al usuario (bajo minimo, vencimiento).
"""

from __future__ import annotations

import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import (
    TimeStampedModel,
    UserStampedModel,
)


class Lot(TimeStampedModel):
    """Lote de un producto con caducidad opcional."""

    product = models.ForeignKey(
        "catalog.Product", on_delete=models.PROTECT, related_name="lots"
    )
    lot_number = models.CharField(max_length=40)
    manufactured_at = models.DateField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        ordering = ["product", "lot_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "lot_number"],
                name="inventory_lot_unique_per_product",
            )
        ]

    def __str__(self) -> str:
        """Devuelve ``producto/lote``."""
        return f"{self.product.sku}/{self.lot_number}"

    @property
    def is_expired(self) -> bool:
        """Indica si el lote ya vencio."""
        return bool(self.expires_at and self.expires_at < datetime.date.today())

    @property
    def days_to_expire(self) -> int | None:
        """Devuelve los dias restantes hasta vencer (o ``None``)."""
        if not self.expires_at:
            return None
        return (self.expires_at - datetime.date.today()).days


class Stock(models.Model):
    """Existencia por ``(producto, ubicacion, lote)``.

    Solo se modifica desde ``InventoryService``. ``save`` directo
    esta bloqueado en ``services``.
    """

    product = models.ForeignKey(
        "catalog.Product", on_delete=models.PROTECT, related_name="stocks"
    )
    location = models.ForeignKey(
        "warehouses.Location",
        on_delete=models.PROTECT,
        related_name="stocks",
    )
    lot = models.ForeignKey(
        Lot,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="stocks",
    )
    quantity = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        default=Decimal("0"),
        validators=[MinValueValidator(0)],
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Existencia"
        verbose_name_plural = "Existencias"
        ordering = ["product", "location"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "location", "lot"],
                name="inventory_stock_unique_combo",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=0),
                name="inventory_stock_quantity_nonneg",
            ),
        ]

    def __str__(self) -> str:
        """Devuelve ``producto@ubicacion``."""
        return f"{self.product.sku}@{self.location.code}"


class StockMovement(TimeStampedModel):
    """Movimiento inmutable de stock.

    Se crea con un servicio dentro de ``transaction.atomic``. Despues
    de persistido no se permite modificar (inmutable).
    """

    class MovementType(models.TextChoices):
        """Tipo de movimiento."""

        RECEIPT = "RECEIPT", "Recepcion"
        ISSUE = "ISSUE", "Salida"
        TRANSFER = "TRANSFER", "Transferencia"
        ADJUSTMENT_IN = "ADJUSTMENT_IN", "Ajuste +"
        ADJUSTMENT_OUT = "ADJUSTMENT_OUT", "Ajuste -"

    class Reason(models.TextChoices):
        """Razon del movimiento."""

        PURCHASE = "PURCHASE", "Compra"
        SALE = "SALE", "Venta"
        DAMAGE = "DAMAGE", "Danio"
        LOSS = "LOSS", "Perdida"
        COUNT = "COUNT", "Conteo"
        CORRECTION = "CORRECTION", "Correccion"
        INTERNAL = "INTERNAL", "Uso interno"
        OTHER = "OTHER", "Otro"

    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.PROTECT, related_name="movements"
    )
    lot = models.ForeignKey(
        Lot,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movements",
    )
    from_location = models.ForeignKey(
        "warehouses.Location",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="outbound_movements",
    )
    to_location = models.ForeignKey(
        "warehouses.Location",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="inbound_movements",
    )
    quantity = models.DecimalField(
        max_digits=14, decimal_places=3, validators=[MinValueValidator(0)]
    )
    unit_cost = models.DecimalField(
        max_digits=14, decimal_places=4, default=Decimal("0")
    )
    reason = models.CharField(max_length=12, choices=Reason.choices)
    reference = models.CharField(max_length=80, blank=True)
    note = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="+",
    )

    class Meta:
        verbose_name = "Movimiento de stock"
        verbose_name_plural = "Movimientos de stock"
        ordering = ["-created_at"]

    def clean(self) -> None:
        """Valida que la combinacion tipo/ubicacion sea coherente."""
        super().clean()
        if self.movement_type in ("RECEIPT", "ADJUSTMENT_IN") and not self.to_location_id:
            raise ValidationError(
                {"to_location": "Requerido para entradas y ajustes +."}
            )
        if self.movement_type in ("ISSUE", "ADJUSTMENT_OUT") and not self.from_location_id:
            raise ValidationError(
                {"from_location": "Requerido para salidas y ajustes -."}
            )
        if self.movement_type == "TRANSFER":
            if not (self.from_location_id and self.to_location_id):
                raise ValidationError(
                    "Transferencia requiere origen y destino."
                )
            if self.from_location_id == self.to_location_id:
                raise ValidationError(
                    {"to_location": "Debe diferir del origen."}
                )

    def save(self, *args, **kwargs):
        """Bloquea la modificacion una vez persistido el movimiento."""
        if self.pk and StockMovement.objects.filter(pk=self.pk).exists():
            raise ValidationError("Los movimientos son inmutables.")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Devuelve ``tipo: producto cantidad``."""
        return f"{self.movement_type}: {self.product.sku} {self.quantity}"


class CycleCount(UserStampedModel):
    """Conteo ciclico de inventario."""

    class Status(models.TextChoices):
        """Estado del conteo."""

        DRAFT = "DRAFT", "Borrador"
        IN_PROGRESS = "IN_PROGRESS", "En progreso"
        APPROVED = "APPROVED", "Aprobado"
        CANCELLED = "CANCELLED", "Cancelado"

    code = models.CharField(max_length=20, unique=True)
    warehouse = models.ForeignKey(
        "warehouses.Warehouse", on_delete=models.PROTECT, related_name="cycle_counts"
    )
    location = models.ForeignKey(
        "warehouses.Location",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cycle_counts",
    )
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.DRAFT
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Conteo ciclico"
        verbose_name_plural = "Conteos ciclicos"
        ordering = ["-code"]


class CycleCountLine(models.Model):
    """Linea de un conteo ciclico."""

    cycle_count = models.ForeignKey(
        CycleCount, on_delete=models.CASCADE, related_name="lines"
    )
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.PROTECT, related_name="+"
    )
    location = models.ForeignKey(
        "warehouses.Location", on_delete=models.PROTECT, related_name="+"
    )
    lot = models.ForeignKey(
        Lot, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    expected_quantity = models.DecimalField(max_digits=14, decimal_places=3)
    counted_quantity = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Linea de conteo"
        verbose_name_plural = "Lineas de conteo"

    @property
    def difference(self) -> Decimal | None:
        """Diferencia ``counted - expected`` o ``None`` si no se conto."""
        if self.counted_quantity is None:
            return None
        return self.counted_quantity - self.expected_quantity


class Alert(TimeStampedModel):
    """Aviso al usuario (bajo minimo, vencimiento, expirado)."""

    class AlertType(models.TextChoices):
        """Tipo de alerta."""

        LOW_STOCK = "LOW_STOCK", "Stock bajo minimo"
        EXPIRING = "EXPIRING", "Proximo a expirar"
        EXPIRED = "EXPIRED", "Expirado"

    alert_type = models.CharField(max_length=10, choices=AlertType.choices)
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="alerts"
    )
    lot = models.ForeignKey(
        Lot, on_delete=models.CASCADE, null=True, blank=True, related_name="alerts"
    )
    message = models.CharField(max_length=200)
    is_read = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"
        ordering = ["-created_at"]


__all__ = [
    "Lot",
    "Stock",
    "StockMovement",
    "CycleCount",
    "CycleCountLine",
    "Alert",
]
