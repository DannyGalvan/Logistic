"""Servicios de la app ``quality``."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.conf import settings

from .catalog import MessageCatalog
from .models import LintMessageRecord, LintRun
from .parser import Json2Parser, LintResult
from .runner import RawLintOutput, SubprocessPylintRunner


@dataclass(frozen=True)
class RunComparison:
    """Delta entre dos corridas."""

    run_a_id: int
    run_b_id: int
    score_delta: float | None
    count_deltas: dict[str, int]


# Bits del exit code de Pylint: 1 fatal, 2 error, 4 warning, 8 refactor,
# 16 convention, 32 error de uso. Solo 1 y 32 implican que el analisis fallo.
FAILURE_EXIT_BITS = 1 | 32


def run_status(exit_code: int) -> str:
    """``SUCCESS`` si Pylint completo el analisis, ``FAILED`` si no."""
    return "FAILED" if exit_code & FAILURE_EXIT_BITS else "SUCCESS"


class LintService:
    """API de ejecucion y analisis de Pylint."""

    def __init__(
        self,
        runner: Any | None = None,
        parser: Any | None = None,
        catalog: Any | None = None,
    ) -> None:
        """Inicializa runner, parser y catalogo."""
        self.runner = runner or SubprocessPylintRunner()
        self.parser = parser or Json2Parser()
        self.catalog = catalog or MessageCatalog()

    def run_project(
        self,
        targets: list[str] | None = None,
        user: Any = None,
        source: str = "WEB",
    ) -> LintRun:
        """Ejecuta Pylint sobre ``targets`` y persiste la corrida."""
        targets = targets or list(getattr(settings, "PYLINT_TARGETS", ["apps", "config"]))
        output = self.runner.run(targets)
        result = self.parser.parse(output)
        run = self._persist(result, output, target=",".join(targets), user=user, source=source)
        return run

    def analyze_snippet(
        self,
        code: str,
        filename: str = "snippet.py",
        user: Any = None,
    ) -> tuple[LintResult, str | None]:
        """Analiza un snippet de codigo sin persistir mensajes."""
        max_bytes = int(getattr(settings, "PYLINT_SNIPPET_MAX_BYTES", 20000))
        if len(code.encode("utf-8")) > max_bytes:
            raise ValueError(
                f"El snippet excede el tamano maximo ({max_bytes} bytes)."
            )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp) / filename
            tmp_path.write_text(code, encoding="utf-8")
            output = self.runner.run([str(tmp_path)])
        result = self.parser.parse(output)
        return result, None

    def compare(self, run_a: LintRun, run_b: LintRun) -> RunComparison:
        """Compara dos corridas y devuelve el delta."""
        score_delta: float | None = None
        if run_a.score is not None and run_b.score is not None:
            score_delta = float(run_b.score) - float(run_a.score)
        count_keys = (
            "convention",
            "refactor",
            "warning",
            "error",
            "fatal",
            "info",
        )
        deltas: dict[str, int] = {}
        for key in count_keys:
            deltas[key] = getattr(run_b, f"{key}_count") - getattr(
                run_a, f"{key}_count"
            )
        return RunComparison(
            run_a_id=run_a.pk,
            run_b_id=run_b.pk,
            score_delta=score_delta,
            count_deltas=deltas,
        )

    def _persist(
        self,
        result: LintResult,
        output: RawLintOutput,
        *,
        target: str,
        user: Any,
        source: str,
    ) -> LintRun:
        """Persiste el resultado en la BD."""
        run = LintRun.objects.create(
            target=target,
            status=run_status(output.exit_code),
            score=result.score,
            convention_count=result.counts.get("convention", 0),
            refactor_count=result.counts.get("refactor", 0),
            warning_count=result.counts.get("warning", 0),
            error_count=result.counts.get("error", 0),
            fatal_count=result.counts.get("fatal", 0),
            info_count=result.counts.get("info", 0),
            modules_linted=int(result.counts.get("module", 0)),
            duration_ms=result.duration_ms,
            triggered_by=user,
            source=source,
            error_detail=output.stderr[:1000] if output.stderr else "",
        )
        LintMessageRecord.objects.bulk_create([
            LintMessageRecord(
                run=run,
                type=msg.type,
                message_id=msg.message_id,
                symbol=msg.symbol,
                message_text=msg.message,
                module=msg.module,
                obj=msg.obj,
                path=msg.path,
                line=msg.line,
                column=msg.column,
            )
            for msg in result.messages
        ])
        return run


__all__ = ["LintService", "RunComparison", "run_status"]
