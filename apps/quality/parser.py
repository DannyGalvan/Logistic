"""Parser de la salida ``json2`` de Pylint."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .runner import RawLintOutput


@dataclass(frozen=True)
class LintMessage:
    """Mensaje individual emitido por Pylint."""

    type: str
    message_id: str
    symbol: str
    message: str
    module: str
    obj: str
    path: str
    line: int
    column: int

    @property
    def category(self) -> str:
        """Letra de la categoria (``C``, ``R``, ``W``, ``E``, ``F``, ``I``)."""
        if not self.message_id:
            return ""
        return self.message_id[0].upper()


@dataclass(frozen=True)
class LintResult:
    """Resultado agregado de una corrida de Pylint."""

    score: float | None
    messages: tuple[LintMessage, ...]
    counts: dict[str, int]
    duration_ms: int
    raw_output: str
    exit_code: int


class Json2Parser:
    """Parser del formato ``json2``."""

    def parse(
        self,
        output: RawLintOutput,
    ) -> LintResult:
        """Convierte la salida cruda a ``LintResult``."""
        try:
            payload: dict[str, Any] = json.loads(output.stdout or "{}")
        except json.JSONDecodeError:
            payload = {}
        messages: list[LintMessage] = []
        for msg in payload.get("messages", []):
            messages.append(
                LintMessage(
                    type=str(msg.get("type", "")),
                    message_id=str(msg.get("messageId", "")),
                    symbol=str(msg.get("symbol", "")),
                    message=str(msg.get("message", "")),
                    module=str(msg.get("module", "")),
                    obj=str(msg.get("obj", "")),
                    path=str(msg.get("path", "")),
                    line=int(msg.get("line", 0) or 0),
                    column=int(msg.get("column", 0) or 0),
                )
            )
        statistics = payload.get("statistics", {})
        counts_raw = statistics.get("messageTypeCount", {})
        counts = {str(k): int(v) for k, v in counts_raw.items()}
        counts.setdefault("module", int(statistics.get("modulesLinted", 0) or 0))
        score_raw = statistics.get("score")
        score = float(score_raw) if score_raw is not None else None
        return LintResult(
            score=score,
            messages=tuple(messages),
            counts=counts,
            duration_ms=output.duration_ms,
            raw_output=output.stdout,
            exit_code=output.exit_code,
        )


__all__ = ["LintMessage", "LintResult", "Json2Parser"]
