"""Estructuras de datos para exportadores."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TabularData:
    """Datos tabulares listos para exportacion.

    Atributos:
        title: Titulo del reporte.
        headers: Lista de encabezados.
        rows: Filas (cada fila es una lista de valores).
        filename: Nombre de archivo sugerido (sin extension).
    """

    title: str
    headers: list[str]
    rows: list[list[Any]]
    filename: str


__all__ = ["TabularData"]
