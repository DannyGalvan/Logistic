"""Serializers de ``inventory``: salida (modelos) y entrada (acciones)."""

from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import Product
from apps.warehouses.models import Location, Warehouse

from ..models import CycleCount, CycleCountLine, Lot, Stock, StockMovement


class LotSerializer(serializers.ModelSerializer):
    """Lote de un producto."""

    class Meta:
        model = Lot
        fields = ["id", "product", "lot_number", "manufactured_at", "expires_at"]


class StockSerializer(serializers.ModelSerializer):
    """Existencia por producto, ubicacion y lote."""

    class Meta:
        model = Stock
        fields = ["id", "product", "location", "lot", "quantity", "updated_at"]


class StockMovementSerializer(serializers.ModelSerializer):
    """Movimiento de inventario (inmutable)."""

    class Meta:
        model = StockMovement
        fields = [
            "id", "movement_type", "product", "lot", "from_location", "to_location",
            "quantity", "unit_cost", "reason", "reference", "note", "created_by",
            "created_at",
        ]


class _MovementInput(serializers.Serializer):  # pylint: disable=abstract-method
    """Campos comunes de las acciones de movimiento."""

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3)
    reference = serializers.CharField(required=False, allow_blank=True, default="")


class ReceiveInputSerializer(_MovementInput):  # pylint: disable=abstract-method
    """Entrada de mercancia."""

    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    unit_cost = serializers.DecimalField(max_digits=14, decimal_places=4)
    lot_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    expires_at = serializers.DateField(required=False, allow_null=True)


class IssueInputSerializer(_MovementInput):  # pylint: disable=abstract-method
    """Salida de mercancia."""

    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    lot = serializers.PrimaryKeyRelatedField(
        queryset=Lot.objects.all(), required=False, allow_null=True
    )


class TransferInputSerializer(_MovementInput):  # pylint: disable=abstract-method
    """Transferencia entre ubicaciones."""

    from_location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    to_location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    lot = serializers.PrimaryKeyRelatedField(
        queryset=Lot.objects.all(), required=False, allow_null=True
    )


class AdjustInputSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Ajuste a una cantidad contada."""

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    counted_quantity = serializers.DecimalField(max_digits=14, decimal_places=3)
    lot = serializers.PrimaryKeyRelatedField(
        queryset=Lot.objects.all(), required=False, allow_null=True
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")


class KardexRowSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Fila del kardex valorizado."""

    date = serializers.DateTimeField()
    movement_type = serializers.CharField()
    reference = serializers.CharField()
    entry_qty = serializers.DecimalField(max_digits=14, decimal_places=3)
    exit_qty = serializers.DecimalField(max_digits=14, decimal_places=3)
    balance = serializers.DecimalField(max_digits=14, decimal_places=3)
    unit_cost = serializers.DecimalField(max_digits=14, decimal_places=4)
    balance_value = serializers.DecimalField(max_digits=16, decimal_places=4)


class CycleCountLineSerializer(serializers.ModelSerializer):
    """Linea de conteo."""

    difference = serializers.DecimalField(max_digits=14, decimal_places=3, read_only=True)

    class Meta:
        model = CycleCountLine
        fields = [
            "id", "product", "location", "lot", "expected_quantity",
            "counted_quantity", "difference",
        ]
        read_only_fields = ["product", "location", "lot", "expected_quantity"]


class CycleCountSerializer(serializers.ModelSerializer):
    """Conteo ciclico con sus lineas."""

    lines = CycleCountLineSerializer(many=True, read_only=True)

    class Meta:
        model = CycleCount
        fields = [
            "id", "code", "warehouse", "location", "status", "approved_by",
            "approved_at", "notes", "lines",
        ]
        read_only_fields = ["code", "status", "approved_by", "approved_at", "notes"]


class CycleCountRecordLineSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Cantidad contada de una linea."""

    id = serializers.IntegerField()
    counted_quantity = serializers.DecimalField(
        max_digits=14, decimal_places=3, min_value=0
    )


class CycleCountRecordSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Cantidades contadas: ``{"lines": [{"id": 1, "counted_quantity": "5"}]}``."""

    lines = CycleCountRecordLineSerializer(many=True, allow_empty=False)


class KardexQuerySerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Filtros del kardex."""

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    warehouse = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(), required=False, allow_null=True
    )
    date_from = serializers.DateField(required=False, allow_null=True)
    date_to = serializers.DateField(required=False, allow_null=True)
