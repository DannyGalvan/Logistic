"""Tests de catalog y parser del modulo quality."""

from __future__ import annotations

import json

from apps.quality.catalog import MessageCatalog
from apps.quality.parser import Json2Parser
from apps.quality.runner import RawLintOutput


def test_catalog_lookup_by_code() -> None:
    """``lookup`` encuentra una entrada por codigo."""
    catalog = MessageCatalog()
    entry = catalog.lookup("E1101")
    assert entry is not None
    assert entry["category"] == "E"


def test_catalog_lookup_by_symbol() -> None:
    """``lookup`` tambien acepta el simbolo (``no-member``)."""
    catalog = MessageCatalog()
    entry = catalog.lookup("no-member")
    assert entry is not None
    assert entry["code"] == "E1101"


def test_catalog_search_term() -> None:
    """``search`` filtra por texto libre."""
    catalog = MessageCatalog()
    results = catalog.search("valor")
    assert results  # al menos una entrada


def test_catalog_by_category() -> None:
    """``by_category`` devuelve solo entradas de la categoria."""
    catalog = MessageCatalog()
    results = catalog.by_category("C")
    assert all(e["category"] == "C" for e in results)


def test_parser_parses_json2_output() -> None:
    """El parser convierte json2 crudo en ``LintResult``."""
    payload = {
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
            "messageTypeCount": {"convention": 1},
            "modulesLinted": 1,
            "score": 9.8,
        },
    }
    raw = RawLintOutput(
        stdout=json.dumps(payload),
        stderr="",
        exit_code=0,
        duration_ms=120,
    )
    result = Json2Parser().parse(raw)
    assert result.score == 9.8
    assert len(result.messages) == 1
    assert result.messages[0].message_id == "C0114"


def test_parser_handles_invalid_json() -> None:
    """JSON invalido -> resultado vacio sin lanzar."""
    raw = RawLintOutput(stdout="not-json", stderr="", exit_code=2, duration_ms=10)
    result = Json2Parser().parse(raw)
    assert not result.messages
    assert result.score is None
