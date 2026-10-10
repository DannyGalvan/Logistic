"""ViewSets de ``catalog``."""

from __future__ import annotations

from apps.core.api.viewsets import ServiceModelViewSet

from .. import services
from ..models import Brand, Category, Product, UnitOfMeasure
from . import serializers


class CategoryViewSet(ServiceModelViewSet):
    """Categorias."""

    queryset = Category.objects.order_by("name")
    serializer_class = serializers.CategorySerializer
    create_service = services.create_category
    update_service = services.update_category
    service_accepts_user = False
    search_fields = ["name"]
    filterset_fields = ["is_active", "parent"]


class BrandViewSet(ServiceModelViewSet):
    """Marcas."""

    queryset = Brand.objects.order_by("name")
    serializer_class = serializers.BrandSerializer
    create_service = services.create_brand
    update_service = services.update_brand
    service_accepts_user = False
    search_fields = ["name"]


class UnitOfMeasureViewSet(ServiceModelViewSet):
    """Unidades de medida."""

    queryset = UnitOfMeasure.objects.order_by("code")
    serializer_class = serializers.UnitOfMeasureSerializer
    create_service = services.create_unit
    update_service = services.update_unit
    service_accepts_user = False
    search_fields = ["code", "name"]


class ProductViewSet(ServiceModelViewSet):
    """Productos."""

    queryset = Product.objects.select_related("category", "brand", "uom").order_by("sku")
    serializer_class = serializers.ProductSerializer
    create_service = services.create_product
    update_service = services.update_product
    search_fields = ["sku", "name", "barcode"]
    filterset_fields = ["category", "brand", "is_active", "track_lots"]
    ordering_fields = ["sku", "name", "sale_price"]
