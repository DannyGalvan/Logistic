"""Tests del comando ``generate_uml``."""

from __future__ import annotations

import subprocess
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

RUN = "apps.quality.management.commands.generate_uml.subprocess.run"


def _done(returncode: int = 0) -> subprocess.CompletedProcess:
    """Resultado simulado de ``pyreverse``."""
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout="", stderr="boom")


def test_generate_uml_runs_pyreverse_per_app(tmp_path) -> None:
    """Una invocacion por app con el formato pedido."""
    out = StringIO()
    with patch(RUN, return_value=_done()) as fake:
        call_command("generate_uml", "--apps", "core", "sales",
                     "--output", str(tmp_path), stdout=out)
    assert fake.call_count == 2
    assert "mmd" in fake.call_args.args[0]
    assert "Diagramas generados" in out.getvalue()


def test_generate_uml_reports_pyreverse_failure(tmp_path) -> None:
    """Un error de ``pyreverse`` se convierte en ``CommandError``."""
    with patch(RUN, return_value=_done(returncode=1)):
        with pytest.raises(CommandError, match="boom"):
            call_command("generate_uml", "--apps", "core", "--output", str(tmp_path))


def test_generate_uml_image_formats_need_graphviz(tmp_path) -> None:
    """PNG/SVG sin ``dot`` instalado falla con un mensaje claro."""
    with patch("apps.quality.management.commands.generate_uml.shutil.which",
               return_value=None):
        with pytest.raises(CommandError, match="Graphviz"):
            call_command("generate_uml", "--format", "png", "--output", str(tmp_path))
