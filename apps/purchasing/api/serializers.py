"""Serializers de ``purchasing``."""

from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import Product
from apps.warehouses.models import Location

from ..models import GoodsReceipt, GoodsReceiptLine, PurchaseOrder, PurchaseOrderLine


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    """Linea de OC."""

    pending_quantity = serializers.DecimalField(
        max_digits=14, decimal_places=3, read_only=True
    )

    class Meta:
        model = PurchaseOrderLine
        fields = ["id", "product", "quantity", "unit_cost", "received_quantity",
                  "pending_quantity"]
        read_only_fields = ["received_quantity"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """OC con lineas; las lineas iniciales se envian al crearla."""

    lines = PurchaseOrderLineSerializer(many=True, required=False)
    total = serializers.DecimalField(max_digits=16, decimal_places=4, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ["id", "code", "supplier", "warehouse", "status", "order_date",
                  "expected_date", "notes", "lines", "total"]
        read_only_fields = ["code", "status"]


class PurchaseAddLineSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Linea a agregar en borrador."""

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3)
    unit_cost = serializers.DecimalField(max_digits=14, decimal_places=4)


class ReceiptLineInputSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Linea de recepcion."""

    order_line_id = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3)
    lot_number = serializers.CharField(required=False, allow_blank=True, default="")
    expires_at = serializers.DateField(required=False, allow_null=True, default=None)


class PurchaseReceiveInputSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Recepcion parcial o total."""

    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    lines = ReceiptLineInputSerializer(many=True, allow_empty=False)


class GoodsReceiptLineSerializer(serializers.ModelSerializer):
    """Linea recibida."""

    class Meta:
        model = GoodsReceiptLine
        fields = ["id", "order_line", "quantity", "lot_number", "expires_at", "movement"]


class GoodsReceiptSerializer(serializers.ModelSerializer):
    """Recepcion (REC)."""

    lines = GoodsReceiptLineSerializer(many=True, read_only=True)

    class Meta:
        model = GoodsReceipt
        fields = ["id", "code", "order", "location", "received_at", "lines"]
