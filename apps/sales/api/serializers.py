"""Serializers de ``sales``."""

from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import Product

from ..models import SalesOrder, SalesOrderLine, Shipment, ShipmentLine


class SalesOrderLineSerializer(serializers.ModelSerializer):
    """Linea de OV."""

    pending_quantity = serializers.DecimalField(
        max_digits=14, decimal_places=3, read_only=True
    )

    class Meta:
        model = SalesOrderLine
        fields = ["id", "product", "quantity", "unit_price", "shipped_quantity",
                  "pending_quantity"]
        read_only_fields = ["shipped_quantity"]


class SalesOrderSerializer(serializers.ModelSerializer):
    """OV con lineas; las lineas iniciales se envian al crearla."""

    lines = SalesOrderLineSerializer(many=True, required=False)
    total = serializers.DecimalField(max_digits=16, decimal_places=4, read_only=True)

    class Meta:
        model = SalesOrder
        fields = ["id", "code", "customer", "warehouse", "status", "order_date",
                  "notes", "lines", "total"]
        read_only_fields = ["code", "status"]


class SalesAddLineSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Linea a agregar en borrador."""

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3)
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=4)


class PickingSuggestionSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Sugerencia de picking (FIFO/FEFO)."""

    order_line_id = serializers.IntegerField()
    location_id = serializers.IntegerField()
    lot_id = serializers.IntegerField(allow_null=True)
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3)


class ShipInputSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Despacho: lineas con ubicacion/lote (usar ``suggest-picking``)."""

    lines = PickingSuggestionSerializer(many=True, allow_empty=False)
    carrier = serializers.CharField(required=False, allow_blank=True, default="")
    tracking_number = serializers.CharField(required=False, allow_blank=True, default="")


class ShipmentLineSerializer(serializers.ModelSerializer):
    """Linea despachada."""

    class Meta:
        model = ShipmentLine
        fields = ["id", "order_line", "location", "lot", "quantity", "movement"]


class ShipmentSerializer(serializers.ModelSerializer):
    """Despacho (DES)."""

    lines = ShipmentLineSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = ["id", "code", "order", "shipped_at", "carrier", "tracking_number", "lines"]
