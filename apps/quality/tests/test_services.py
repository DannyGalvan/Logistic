"""Tests del ``LintService``."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from apps.quality.models import LintMessageRecord, LintRun
from apps.quality.parser import Json2Parser
from apps.quality.runner import RawLintOutput
from apps.quality.services import LintService


def _fake_payload(score: float = 9.8, counts: dict | None = None) -> dict:
    """Genera un payload ``json2`` minimo."""
    return {
        "messages": [
            {
                "type": "convention",
                "messageId": "C0114",
                "symbol": "missing-module-docstring",
                "message": "Missing module docstring",
                "module": "demo",
                "obj": "",
                "path": "demo.py",
                "line": 1,
                "column": 0,
            }
        ],
        "statistics": {
            "messageTypeCount": counts or {"convention": 1, "module": 1},
            "score": score,
        },
    }


@pytest.fixture
def fake_runner() -> MagicMock:
    """Devuelve un ``LintRunner`` simulado."""
    runner = MagicMock()
    runner.run.return_value = RawLintOutput(
        stdout=json.dumps(_fake_payload(score=9.9)),
        stderr="",
        exit_code=0,
        duration_ms=120,
    )
    return runner


@pytest.fixture
def service(fake_runner) -> LintService:
    """Devuelve un servicio con dependencias mockeadas."""
    return LintService(runner=fake_runner, parser=Json2Parser())


@pytest.mark.django_db
def test_run_project_persists_run(service) -> None:
    """``run_project`` crea una corrida con mensajes."""
    run = service.run_project(targets=["apps"], user=None, source="CLI")
    assert isinstance(run, LintRun)
    assert run.messages.count() == 1
    assert LintMessageRecord.objects.filter(run=run).count() == 1


@pytest.mark.django_db
def test_compare_returns_delta(service) -> None:
    """``compare`` devuelve un delta entre dos corridas."""
    a = service.run_project(targets=["apps"], user=None, source="CLI")
    b = service.run_project(targets=["apps"], user=None, source="CLI")
    comparison = service.compare(a, b)
    assert comparison.run_a_id == a.pk
    assert comparison.run_b_id == b.pk


@pytest.mark.django_db
def test_analyze_snippet_returns_result(fake_runner) -> None:
    """``analyze_snippet`` devuelve el resultado sin persistir."""
    fake_runner.run.return_value = RawLintOutput(
        stdout=json.dumps(_fake_payload(score=10.0)),
        stderr="",
        exit_code=0,
        duration_ms=10,
    )
    service = LintService(runner=fake_runner, parser=Json2Parser())
    result, _ = service.analyze_snippet(code="print('hi')")
    assert result.score == 10.0


def test_analyze_snippet_rejects_oversize() -> None:
    """``analyze_snippet`` rechaza snippets demasiado grandes."""
    service = LintService()
    with pytest.raises(ValueError):
        service.analyze_snippet(code="x" * 50000)
