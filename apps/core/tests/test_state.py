"""Tests de ``apps.core.state.StateMachine``."""

from __future__ import annotations

import pytest

from apps.core.exceptions import InvalidStateTransitionError
from apps.core.state import StateMachine


def test_can_transition_returns_true_for_allowed_pair() -> None:
    """Una transicion declarada como valida debe ser permitida."""
    machine = StateMachine({"DRAFT": ["CONFIRMED", "CANCELLED"]})
    assert machine.can_transition("DRAFT", "CONFIRMED") is True
    assert machine.can_transition("DRAFT", "CANCELLED") is True


def test_can_transition_returns_false_for_unknown_pair() -> None:
    """Una transicion no declarada debe rechazarse."""
    machine = StateMachine({"DRAFT": ["CONFIRMED"]})
    assert machine.can_transition("DRAFT", "RECEIVED") is False
    assert machine.can_transition("CONFIRMED", "DRAFT") is False


def test_assert_can_transition_raises_for_invalid() -> None:
    """``assert_can_transition`` lanza ``InvalidStateTransitionError``."""
    machine = StateMachine({"DRAFT": ["CONFIRMED"]})
    with pytest.raises(InvalidStateTransitionError):
        machine.assert_can_transition("DRAFT", "RECEIVED")


def test_allowed_targets_returns_immutable_view() -> None:
    """``allowed_targets`` debe ser un ``frozenset`` inmutable."""
    machine = StateMachine({"DRAFT": ["CONFIRMED", "CANCELLED"]})
    targets = machine.allowed_targets("DRAFT")
    assert isinstance(targets, frozenset)
    assert "CONFIRMED" in targets
    assert "CANCELLED" in targets


def test_allow_adds_transitions_after_init() -> None:
    """``allow`` debe extender las transiciones en caliente."""
    machine = StateMachine()
    machine.allow("A", ["C"])
    assert machine.can_transition("A", "C") is True
