"""Tests de ``apps.core.models.next_code`` y ``DocumentSequence``."""

from __future__ import annotations

import pytest

from apps.core.models import DocumentSequence, next_code


@pytest.mark.django_db
def test_next_code_creates_sequence_on_first_use() -> None:
    """Si no existe la secuencia, ``next_code`` la crea con prefijo."""
    code = next_code("OC")
    assert code == "OC-000001"
    assert DocumentSequence.objects.filter(prefix="OC").exists()


@pytest.mark.django_db
def test_next_code_increments_existing_sequence() -> None:
    """Llamadas sucesivas incrementan el correlativo."""
    first = next_code("OV")
    second = next_code("OV")
    third = next_code("OV")
    assert first == "OV-000001"
    assert second == "OV-000002"
    assert third == "OV-000003"


@pytest.mark.django_db
def test_next_code_uses_six_digit_padding() -> None:
    """El formato del codigo debe tener padding a 6 digitos."""
    code = next_code("REC")
    assert len(code.split("-")[1]) == 6
    assert code == "REC-000001"


@pytest.mark.django_db
def test_document_sequence_str_uses_padding() -> None:
    """El ``__str__`` de la secuencia debe usar padding a 6 digitos."""
    DocumentSequence.objects.create(prefix="PR", last_number=42)
    sequence = DocumentSequence.objects.get(prefix="PR")
    assert str(sequence) == "PR-000042"
