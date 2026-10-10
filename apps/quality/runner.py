"""Adapter que envuelve el ejecutable de Pylint.

``LintRunner`` es un Protocol; ``SubprocessPylintRunner`` es la
implementacion por defecto que lanza ``python -m pylint`` en un
subproceso y devuelve la salida cruda.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Protocol

from django.conf import settings


class LintExecutionError(Exception):
    """La ejecucion de Pylint fallo (timeout, OOM, etc.)."""


class RawLintOutput:
    """Salida cruda del runner."""

    def __init__(self, stdout: str, stderr: str, exit_code: int, duration_ms: int) -> None:
        """Inicializa con los datos del subproceso."""
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.duration_ms = duration_ms


class LintRunner(Protocol):
    """Contrato del runner."""

    def run(self, targets: list[str]) -> RawLintOutput:
        """Ejecuta Pylint sobre ``targets`` y devuelve la salida cruda."""


class SubprocessPylintRunner:
    """Implementacion que invoca ``python -m pylint`` via subprocess."""

    def __init__(
        self,
        rcfile: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """Inicializa con la ruta del rcfile y el timeout."""
        self.rcfile = rcfile or getattr(settings, "PYLINT_RCFILE", ".pylintrc")
        self.timeout = timeout or int(getattr(settings, "PYLINT_TIMEOUT", 180))

    def run(self, targets: list[str]) -> RawLintOutput:
        """Lanza Pylint y captura stdout/stderr."""
        args = [
            sys.executable, "-m", "pylint",
            "--output-format=json2",
            f"--rcfile={self.rcfile}",
            *targets,
        ]
        cwd = Path(settings.BASE_DIR) if hasattr(settings, "BASE_DIR") else Path.cwd()
        if all(Path(target).is_file() for target in targets):
            # Archivos sueltos (snippets): sin paralelismo; con ``jobs=0``
            # Pylint 4 falla al analizar rutas fuera del proyecto.
            args.insert(-len(targets), "--jobs=1")
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(
            filter(None, [str(cwd), os.environ.get("PYTHONPATH", "")])
        )}
        started = time.monotonic()
        try:
            completed = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(cwd),
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise LintExecutionError(
                f"Pylint excedio el timeout de {self.timeout}s."
            ) from exc
        duration_ms = int((time.monotonic() - started) * 1000)
        return RawLintOutput(
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_code=completed.returncode,
            duration_ms=duration_ms,
        )


def _safe_load_json(stdout: str) -> dict:
    """Carga JSON de ``stdout``; devuelve dict vacio si falla."""
    try:
        return json.loads(stdout or "{}")
    except json.JSONDecodeError:
        return {}


__all__ = [
    "LintRunner",
    "SubprocessPylintRunner",
    "RawLintOutput",
    "LintExecutionError",
    "_safe_load_json",
]
