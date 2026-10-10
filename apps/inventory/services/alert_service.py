"""Servicios de alertas de inventario.

``AlertService`` mantiene vigentes las alertas ``LOW_STOCK`` y las
relacionadas con la caducidad de lotes.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.utils.timezone import now

from apps.inventory.models import Alert, Lot, Stock


class AlertService:
    """API de gestion de alertas."""

    def evaluate_product(self, product: Any) -> None:
        """Crea o resuelve alertas ``LOW_STOCK`` para un producto."""
        on_hand = sum(
            (s.quantity for s in Stock.objects.filter(product=product)),
            Decimal("0"),
        )
        active = Alert.objects.filter(
            product=product, alert_type="LOW_STOCK", resolved_at__isnull=True
        )
        if on_hand < product.reorder_point:
            Alert.objects.get_or_create(
                product=product,
                alert_type="LOW_STOCK",
                resolved_at__isnull=True,
                defaults={
                    "message": (
                        f"Stock {on_hand} bajo minimo {product.reorder_point}."
                    ),
                },
            )
        else:
            active.update(resolved_at=now())

    def evaluate_expirations(self, days: int | None = None) -> None:
        """Crea alertas ``EXPIRING``/``EXPIRED`` para lotes proximos."""
        days = days or int(getattr(settings, "EXPIRY_ALERT_DAYS", 30))
        today = datetime.date.today()
        horizon = today + datetime.timedelta(days=days)
        for lot in Lot.objects.exclude(expires_at__isnull=True):
            if lot.expires_at < today:
                Alert.objects.get_or_create(
                    product=lot.product,
                    lot=lot,
                    alert_type="EXPIRED",
                    resolved_at__isnull=True,
                    defaults={"message": f"Lote {lot.lot_number} expirado."},
                )
            elif lot.expires_at <= horizon:
                Alert.objects.get_or_create(
                    product=lot.product,
                    lot=lot,
                    alert_type="EXPIRING",
                    resolved_at__isnull=True,
                    defaults={
                        "message": (
                            f"Lote {lot.lot_number} expira {lot.expires_at}."
                        ),
                    },
                )


__all__ = ["AlertService"]
