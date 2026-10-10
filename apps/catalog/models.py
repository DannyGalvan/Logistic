"""Modelos de la app ``catalog``.

Cuatro modelos principales: ``Category``, ``Brand``, ``UnitOfMeasure``
y ``Product``. ``Product`` hereda de ``UserStampedModel`` y
``ActivatableModel`` para auditoria y desactivacion logica.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import (
    ActivatableModel,
    TimeStampedModel,
    UserStampedModel,
)


class Category(TimeStampedModel, ActivatableModel):
    """Categoria de productos en jerarquia (self-referential)."""

    name = models.CharField(max_length=80, unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
    )
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["name"]

    def __str__(self) -> str:
        """Devuelve el nombre legible de la categoria."""
        return self.name


class Brand(TimeStampedModel, ActivatableModel):
    """Marca comercial del producto."""

    name = models.CharField(max_length=80, unique=True)

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ["name"]

    def __str__(self) -> str:
        """Devuelve el nombre de la marca."""
        return self.name


class UnitOfMeasure(TimeStampedModel, ActivatableModel):
    """Unidad de medida (UND, CJ, KG, LT, ...)."""

    code = models.CharField(max_length=8, unique=True)
    name = models.CharField(max_length=40)

    class Meta:
        verbose_name = "Unidad de medida"
        verbose_name_plural = "Unidades de medida"
        ordering = ["code"]

    def __str__(self) -> str:
        """Devuelve ``code - name`` como representacion legible."""
        return f"{self.code} - {self.name}"


class Product(UserStampedModel, ActivatableModel):
    """Producto del catalogo.

    Atributos:
        cost_price: costo promedio ponderado. Solo lo modifica el
            service de inventario (``InventoryService``).
    """

    class RotationStrategy(models.TextChoices):
        """Estrategia de rotacion de stock."""

        FIFO = "FIFO", "Primero en entrar, primero en salir"
        FEFO = "FEFO", "Primero en expirar, primero en salir"

    sku = models.CharField(max_length=40, unique=True)
    barcode = models.CharField(
        max_length=40, blank=True, null=True, unique=True
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="products",
    )
    uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name="products",
    )
    cost_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
    )
    sale_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
    )
    min_stock = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
    )
    max_stock = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
    )
    reorder_point = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
    )
    track_lots = models.BooleanField(default=False)
    track_expiry = models.BooleanField(default=False)
    rotation_strategy = models.CharField(
        max_length=4,
        choices=RotationStrategy.choices,
        default=RotationStrategy.FIFO,
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["sku"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(min_stock__gte=0),
                name="catalog_product_min_stock_nonneg",
            ),
            models.CheckConstraint(
                condition=models.Q(max_stock__gte=models.F("min_stock")),
                name="catalog_product_max_gte_min",
            ),
        ]

    def __str__(self) -> str:
        """Devuelve ``sku - name``."""
        return f"{self.sku} - {self.name}"

    def clean(self) -> None:
        """Valida que ``track_expiry`` requiera ``track_lots``."""
        super().clean()
        if self.track_expiry and not self.track_lots:
            raise ValidationError(
                {"track_expiry": "Requiere que track_lots este activo."}
            )


__all__ = [
    "Category",
    "Brand",
    "UnitOfMeasure",
    "Product",
]
