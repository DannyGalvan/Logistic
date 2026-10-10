"""Eventos del dominio de inventario (patron Observer).

Se definen aparte de ``signals.py`` para que los services puedan
emitirlos sin importar los receivers (evita imports circulares).
"""

from __future__ import annotations

from django.dispatch import Signal

# Se emite tras cada movimiento con ``product=<Product>``.
stock_changed = Signal()

__all__ = ["stock_changed"]
