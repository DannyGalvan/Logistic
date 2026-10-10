"""Selectors de la app ``inventory``."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Q, QuerySet, Sum

from apps.catalog.models import Product
from apps.core.models import KardexRow
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
    """Productos bajo minimo."""
    return Product.objects.filter(
        reorder_point__gt=0,
    )


def expiring_lots(days: int | None = None) -> QuerySet[Lot]:
    """Lotes que vencen en ``days`` dias (default = config)."""
    days = days or int(getattr(settings, "EXPIRY_ALERT_DAYS", 30))
    today = date.today()
    return Lot.objects.filter(
        expires_at__lte=today + timedelta(days=days),
    ).order_by("expires_at")


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
    for movement in qs:
        if movement.movement_type in ("RECEIPT", "ADJUSTMENT_IN"):
            entry, exit_q = movement.quantity, Decimal("0")
        elif movement.movement_type in ("ISSUE", "ADJUSTMENT_OUT"):
            entry, exit_q = Decimal("0"), movement.quantity
        else:
            entry = movement.quantity
            exit_q = Decimal("0")
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
