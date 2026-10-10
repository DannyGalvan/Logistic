"""Catalogo de mensajes Pylint."""

from __future__ import annotations

from typing import Iterable

from .data import CATALOG


class MessageCatalog:
    """API de busqueda en el catalogo de mensajes."""

    def __init__(self, entries: Iterable[dict] | None = None) -> None:
        """Carga el catalogo en memoria."""
        self.entries: list[dict] = list(entries) if entries else list(CATALOG)

    def lookup(self, code_or_symbol: str) -> dict | None:
        """Busca por codigo o simbolo."""
        target = code_or_symbol.upper()
        for entry in self.entries:
            if entry["code"].upper() == target or entry["symbol"] == code_or_symbol:
                return entry
        return None

    def search(self, term: str) -> list[dict]:
        """Busca por texto libre."""
        lower = term.lower()
        return [
            entry
            for entry in self.entries
            if lower in entry["title"].lower()
            or lower in entry["explanation"].lower()
            or lower in entry["symbol"].lower()
            or lower in entry["code"].lower()
        ]

    def by_category(self, letter: str) -> list[dict]:
        """Devuelve las entradas cuya categoria empieza por ``letter``."""
        letter = letter.upper()
        return [e for e in self.entries if e["category"].upper().startswith(letter)]


__all__ = ["MessageCatalog"]
