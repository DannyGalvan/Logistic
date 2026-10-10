"""Selectors de la app ``inventory``."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Q, QuerySet, Sum

from apps.catalog.models import Product
from apps.core.models import KardexRow
from apps.core.selectors import low_stock_products as core_low_stock_products
from apps.inventory.models import Alert, Lot, Stock, StockMovement


def stock_by_product(product) -> QuerySet[Stock]:
    """Devuelve las existencias de un producto."""
    return Stock.objects.filter(product=product).select_related(
        "location", "lot"
    )


def stock_on_hand(product, warehouse=None) -> Decimal:
    """Suma existencias; opcionalmente filtrando por almacen."""
    qs = Stock.objects.filter(product=product, quantity__gt=0)
    if warehouse is not None:
        qs = qs.filter(location__warehouse=warehouse)
    return qs.aggregate(total=Sum("quantity"))["total"] or Decimal("0")


def low_stock_products() -> QuerySet[Product]:
    """Productos activos cuya existencia total esta bajo ``min_stock``."""
    return core_low_stock_products()


def expiring_lots(days: int | None = None) -> QuerySet[Lot]:
    """Lotes que vencen en ``days`` dias (default = config)."""
    days = days or int(getattr(settings, "EXPIRY_ALERT_DAYS", 30))
    today = date.today()
    return Lot.objects.filter(
        expires_at__lte=today + timedelta(days=days),
    ).order_by("expires_at")


def _kardex_quantities(movement, warehouse) -> tuple[Decimal, Decimal]:
    """Devuelve ``(entrada, salida)`` de un movimiento para el kardex.

    Una transferencia es neutra a nivel global; si se filtra por almacen
    cuenta como entrada o salida segun el lado que pertenezca a el.
    """
    if movement.movement_type in ("RECEIPT", "ADJUSTMENT_IN"):
        return movement.quantity, Decimal("0")
    if movement.movement_type in ("ISSUE", "ADJUSTMENT_OUT"):
        return Decimal("0"), movement.quantity
    if warehouse is None:
        return movement.quantity, movement.quantity
    entry = (
        movement.quantity
        if movement.to_location and movement.to_location.warehouse_id == warehouse.pk
        else Decimal("0")
    )
    exit_q = (
        movement.quantity
        if movement.from_location
        and movement.from_location.warehouse_id == warehouse.pk
        else Decimal("0")
    )
    return entry, exit_q


def kardex(
    product,
    warehouse=None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[KardexRow]:
    """Genera el kardex valorizado para ``product``."""
    qs = StockMovement.objects.filter(product=product).order_by("created_at")
    if warehouse is not None:
        qs = qs.filter(
            Q(from_location__warehouse=warehouse)
            | Q(to_location__warehouse=warehouse)
        )
    if date_from:
        qs = qs.filter(created_at__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__lte=date_to)
    rows: list[KardexRow] = []
    balance = Decimal("0")
    for movement in qs.select_related("from_location", "to_location"):
        entry, exit_q = _kardex_quantities(movement, warehouse)
        balance += entry - exit_q
        rows.append(
            KardexRow(
                date=movement.created_at,
                movement_type=movement.movement_type,
                reference=movement.reference or str(movement.pk),
                entry_qty=entry,
                exit_qty=exit_q,
                balance=balance,
                unit_cost=movement.unit_cost,
                balance_value=balance * movement.unit_cost,
            )
        )
    return rows


def movements(filters: dict | None = None) -> QuerySet[StockMovement]:
    """Lista de movimientos filtrada."""
    qs = StockMovement.objects.select_related(
        "product", "lot", "from_location", "to_location"
    )
    if filters:
        qs = qs.filter(**filters)
    return qs


def unread_alerts() -> QuerySet[Alert]:
    """Alertas no leidas."""
    return Alert.objects.filter(is_read=False, resolved_at__isnull=True)


__all__ = [
    "stock_by_product",
    "stock_on_hand",
    "low_stock_products",
    "expiring_lots",
    "kardex",
    "movements",
    "unread_alerts",
]
