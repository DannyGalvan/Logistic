"""Maquina de estados generica (patron State)."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .exceptions import InvalidStateTransitionError


class StateMachine:
    """Encapsula transiciones validas entre estados.

    Atributos:
        transitions (dict[str, set[str]]): Mapa ``origen -> {destinos}``.
    """

    def __init__(self, transitions: dict[str, Iterable[str]] | None = None) -> None:
        """Inicializa la maquina con un dict de transiciones.

        Args:
            transitions: Dict ``origen -> destinos``. ``None`` inicia vacia.
        """
        self._transitions: dict[str, set[str]] = defaultdict(set)
        if transitions:
            for origin, targets in transitions.items():
                self.allow(origin, list(targets))

    def allow(self, origin: str, targets: Iterable[str]) -> None:
        """Registra destinos permitidos desde ``origin``.

        Args:
            origin: Estado de origen.
            targets: Iterable de destinos validos.
        """
        self._transitions[origin].update(targets)

    def can_transition(self, current: str, target: str) -> bool:
        """Indica si ``current -> target`` es una transicion valida."""
        return target in self._transitions.get(current, set())

    def assert_can_transition(self, current: str, target: str) -> None:
        """Verifica la transicion o lanza ``InvalidStateTransitionError``."""
        if not self.can_transition(current, target):
            raise InvalidStateTransitionError(
                f"No se puede transicionar de '{current}' a '{target}'."
            )

    def allowed_targets(self, current: str) -> frozenset[str]:
        """Devuelve los destinos validos desde ``current`` (inmutable)."""
        return frozenset(self._transitions.get(current, set()))
