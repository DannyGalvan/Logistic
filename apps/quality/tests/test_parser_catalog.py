"""Tests del parser ``json2`` y del catalogo de mensajes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from apps.quality.catalog import MessageCatalog
from apps.quality.parser import Json2Parser
from apps.quality.runner import RawLintOutput
from apps.quality.services import run_status

FIXTURE = Path(__file__).parent / "fixtures" / "pylint_json2.json"


def _output(stdout: str, exit_code: int = 0) -> RawLintOutput:
    """Salida cruda simulada."""
    return RawLintOutput(stdout=stdout, stderr="", exit_code=exit_code, duration_ms=5)


def test_parser_reads_real_json2_fixture() -> None:
    """La salida real de Pylint (``calculos_malo``) se parsea completa."""
    raw = FIXTURE.read_text(encoding="utf-8")
    result = Json2Parser().parse(_output(raw, exit_code=28))
    symbols = {msg.symbol for msg in result.messages}
    assert {"invalid-name", "unused-import", "unused-variable"} <= symbols
    assert result.counts["convention"] == 5
    assert result.counts["module"] == json.loads(raw)["statistics"]["modulesLinted"]
    assert 0 < result.score < 10
    first = result.messages[0]
    assert first.category == first.message_id[0]


def test_parser_tolerates_invalid_json() -> None:
    """JSON invalido produce un resultado vacio, no una excepcion."""
    result = Json2Parser().parse(_output("no es json"))
    assert not result.messages
    assert result.score is None


@pytest.mark.parametrize(
    ("exit_code", "expected"),
    [(0, "SUCCESS"), (28, "SUCCESS"), (2, "SUCCESS"), (1, "FAILED"), (32, "FAILED")],
)
def test_run_status_from_exit_bits(exit_code: int, expected: str) -> None:
    """Solo los bits fatal (1) y uso (32) marcan la corrida como fallida."""
    assert run_status(exit_code) == expected


def test_catalog_lookup_by_code_and_symbol() -> None:
    """El catalogo encuentra por codigo y por simbolo."""
    catalog = MessageCatalog()
    by_code = catalog.lookup("c0103")
    assert by_code is not None
    assert catalog.lookup("invalid-name") == by_code
    assert catalog.lookup("X9999") is None


def test_catalog_search_and_category() -> None:
    """Busqueda libre y filtro por categoria."""
    catalog = MessageCatalog()
    assert any(e["symbol"] == "invalid-name" for e in catalog.search("nombre"))
    assert all(e["category"].startswith("C") for e in catalog.by_category("c"))
    assert MessageCatalog(entries=[{"code": "Z1", "symbol": "z", "category": "Z",
                                    "title": "", "explanation": ""}]).lookup("Z1")
