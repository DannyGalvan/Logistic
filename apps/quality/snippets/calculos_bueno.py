"""Snippet corregido para comparar contra ``calculos_malo.py``."""

from __future__ import annotations

from typing import Iterable


def calcular(a: float, b: float) -> float:
    """Devuelve la suma de dos numeros."""
    return a + b


def divide_numbers(
    valor: float,
    divisor: float,
    lista: list | None = None,
) -> float:
    """Divide ``valor`` por ``divisor`` y suma el ultimo item de la lista."""
    if lista is None:
        lista = []
    try:
        item = lista.pop()
    except IndexError:
        item = 0
    return valor / divisor + item


def procesa(items: Iterable[float]) -> dict[str, float]:
    """Calcula estadisticas agregadas sobre ``items``."""
    valores = list(items)
    if not valores:
        return {"suma": 0, "media": 0, "maximo": 0, "minimo": 0}
    suma = sum(valores)
    media = suma / len(valores)
    return {
        "suma": suma,
        "media": media,
        "maximo": max(valores),
        "minimo": min(valores),
    }
