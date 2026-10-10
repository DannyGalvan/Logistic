"""Tests del comando ``run_pylint``, vistas POST y Pylint real (slow)."""

from __future__ import annotations

from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse

from apps.accounts.roles import Role
from apps.quality.models import LintMessageRecord, LintRun
from apps.quality.parser import LintResult
from apps.quality.services import LintService

pytestmark = pytest.mark.django_db
RUN_PROJECT = "apps.quality.services.LintService.run_project"
SNIPPETS = Path(settings.BASE_DIR) / "apps" / "quality" / "snippets"


def _run(score: str) -> LintRun:
    """Corrida persistida con la nota indicada."""
    return LintRun.objects.create(target="apps", score=Decimal(score))


def test_run_pylint_command_passes_over_threshold() -> None:
    """Nota sobre el umbral: el comando informa la corrida."""
    out = StringIO()
    with patch(RUN_PROJECT, return_value=_run("9.90")):
        call_command("run_pylint", "--fail-under", "9.5", stdout=out)
    assert "nota=9.90" in out.getvalue()


def test_run_pylint_command_fails_under_threshold() -> None:
    """Nota bajo el umbral: ``CommandError`` (exit code != 0)."""
    with patch(RUN_PROJECT, return_value=_run("8.00")):
        with pytest.raises(CommandError, match="por debajo"):
            call_command("run_pylint", "--fail-under", "9.5", stdout=StringIO())


def test_run_pylint_command_wraps_runner_errors() -> None:
    """Errores del runner se convierten en ``CommandError``."""
    with patch(RUN_PROJECT, side_effect=RuntimeError("timeout")):
        with pytest.raises(CommandError, match="timeout"):
            call_command("run_pylint", stdout=StringIO())


def test_run_view_requires_run_lint(client_as) -> None:
    """Consulta no puede ejecutar; Supervisor si."""
    with patch(RUN_PROJECT, return_value=_run("9.70")) as fake:
        assert client_as(Role.VIEWER).post(reverse("quality:run")).status_code == 403
        response = client_as(Role.SUPERVISOR).post(reverse("quality:run"))
    assert response.status_code == 302
    fake.assert_called_once()


def test_run_view_reports_errors(client_as) -> None:
    """Un fallo del runner se muestra como mensaje."""
    with patch(RUN_PROJECT, side_effect=RuntimeError("sin pylint")):
        response = client_as(Role.SUPERVISOR).post(reverse("quality:run"), follow=True)
    assert any("sin pylint" in str(m) for m in response.context["messages"])


def test_run_detail_lists_messages(admin_client) -> None:
    """El detalle muestra los mensajes sin chocar con ``messages``."""
    run = _run("7.00")
    LintMessageRecord.objects.create(
        run=run, type="convention", message_id="C0103", symbol="invalid-name",
        message_text="Nombre", path="a.py", line=1,
    )
    response = admin_client.get(reverse("quality:run-detail", args=[run.pk]))
    assert response.status_code == 200
    assert b"invalid-name" in response.content


def test_snippet_view_analyzes_and_loads_demo(admin_client) -> None:
    """GET con ``demo`` precarga codigo; POST muestra el resultado."""
    demo = admin_client.get(reverse("quality:snippet"), {"demo": "calculos_malo"})
    assert "def Calcular" in demo.context["code"]
    result = LintResult(score=5.0, messages=(), counts={}, duration_ms=1,
                        raw_output="", exit_code=0)
    with patch.object(LintService, "analyze_snippet", return_value=(result, None)):
        response = admin_client.post(reverse("quality:snippet"), {"code": "x = 1\n"})
    assert response.context["result"].score == 5.0


def test_snippet_view_rejects_oversize(admin_client) -> None:
    """Un snippet demasiado grande muestra error y no analiza."""
    response = admin_client.post(reverse("quality:snippet"), {"code": "x" * 50000})
    assert response.context["result"] is None


def test_catalog_view_filters(admin_client) -> None:
    """Busqueda por texto y por categoria."""
    by_text = admin_client.get(reverse("quality:catalog"), {"q": "invalid-name"})
    assert [e["symbol"] for e in by_text.context["entries"]] == ["invalid-name"]
    by_cat = admin_client.get(reverse("quality:catalog"), {"cat": "w"})
    assert all(e["category"] == "W" for e in by_cat.context["entries"])


@pytest.mark.slow
def test_real_pylint_on_demo_snippets() -> None:
    """Pylint real: ``calculos_malo`` falla reglas y ``calculos_bueno`` saca mas."""
    service = LintService()
    bad, _ = service.analyze_snippet(
        code=(SNIPPETS / "calculos_malo.py").read_text(encoding="utf-8"),
        filename="calculos_malo.py",
    )
    good, _ = service.analyze_snippet(
        code=(SNIPPETS / "calculos_bueno.py").read_text(encoding="utf-8"),
        filename="calculos_bueno.py",
    )
    symbols = {msg.symbol for msg in bad.messages}
    assert {"invalid-name", "unused-import"} <= symbols
    assert good.score > bad.score
