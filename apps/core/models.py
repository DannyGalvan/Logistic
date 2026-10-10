"""Modelos abstractos y secuencia de documentos.

Los modelos aqui definidos no crean tablas por si mismos (clase meta
``abstract = True``). Sirven como base para que las apps de dominio
hereden campos y comportamiento comun sin duplicar codigo.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.db import models, transaction

from .managers import ActiveManager


class TimeStampedModel(models.Model):
    """Modelo abstracto con marcas de tiempo automaticas.

    Atributos:
        created_at (datetime): Fecha de creacion, asignada en el primer save.
        updated_at (datetime): Fecha de la ultima modificacion, actualizada
            automaticamente en cada save.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserStampedModel(TimeStampedModel):
    """Modelo abstracto que registra usuario creador y modificador.

    Atributos:
        created_by (User|None): Usuario que creo el registro.
        updated_by (User|None): Usuario que realizo la ultima modificacion.
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        abstract = True


class ActivatableModel(models.Model):
    """Modelo abstracto que admite desactivacion logica.

    Atributos:
        is_active (bool): True cuando el registro esta vigente. Los
            registros desactivados no se borran: se filtran en la UI.
    """

    is_active = models.BooleanField(default=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        abstract = True


class DocumentSequence(models.Model):
    """Secuencia numerica para codigos de documento (OC-000001, OV-...).

    Atributos:
        prefix (str): Prefijo unico del documento (ej. ``"OC"``).
        last_number (int): Ultimo correlativo emitido.
        id (UUID): Identificador primario del registro.
    """

    prefix = models.CharField(max_length=10, unique=True)
    last_number = models.PositiveIntegerField(default=0)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        verbose_name = "Secuencia de documento"
        verbose_name_plural = "Secuencias de documento"
        ordering = ["prefix"]

    def __str__(self) -> str:
        """Devuelve la representacion legible del registro."""
        return f"{self.prefix}-{self.last_number:06d}"


@transaction.atomic
def next_code(prefix: str) -> str:
    """Genera el siguiente codigo para ``prefix`` de forma atomica.

    Args:
        prefix: Prefijo del documento (ej. ``"OC"``).

    Returns:
        Codigo formateado ``"<prefix>-<numero>"`` con padding a 6
        digitos. Garantiza que dos llamadas concurrentes no reciban
        el mismo correlativo mediante ``select_for_update``.
    """
    sequence = (
        DocumentSequence.objects.select_for_update()
        .filter(prefix=prefix).first()
    )
    if sequence is None:
        sequence = DocumentSequence.objects.create(prefix=prefix, last_number=0)
        sequence = (
            DocumentSequence.objects.select_for_update().get(pk=sequence.pk)
        )
    sequence.last_number = sequence.last_number + 1
    sequence.save(update_fields=["last_number"])
    return f"{prefix}-{sequence.last_number:06d}"


class KardexRow:  # pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-positional-arguments
    """DTO inmutable que representa una fila del reporte Kardex.

    Cada ``KardexRow`` agrega los ocho campos de la linea contable:
    identificacion del movimiento, cantidades de entrada/salida, saldo
    y valoracion. Agruparlos en otro DTO restaria claridad al reporte,
    por lo que se documenta la decision inline.
    """

    __slots__ = (
        "date",
        "movement_type",
        "reference",
        "entry_qty",
        "exit_qty",
        "balance",
        "unit_cost",
        "balance_value",
    )

    def __init__(
        self,
        date: Any,
        movement_type: str,
        reference: str,
        entry_qty: Decimal,
        exit_qty: Decimal,
        balance: Decimal,
        unit_cost: Decimal,
        balance_value: Decimal,
    ) -> None:
        """Inicializa la fila con valores validados."""
        self.date = date
        self.movement_type = movement_type
        self.reference = reference
        self.entry_qty = entry_qty
        self.exit_qty = exit_qty
        self.balance = balance
        self.unit_cost = unit_cost
        self.balance_value = balance_value
