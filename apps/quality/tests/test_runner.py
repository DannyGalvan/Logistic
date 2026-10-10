"""Tests de ``SubprocessPylintRunner`` con subprocess mockeado."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import patch

import pytest

from apps.quality.runner import (
    LintExecutionError,
    RawLintOutput,
    SubprocessPylintRunner,
)


def test_runner_returns_raw_output() -> None:
    """El runner invoca subprocess y devuelve RawLintOutput."""
    fake = subprocess.CompletedProcess(
        args=[], returncode=0,
        stdout=json.dumps({"messages": [], "statistics": {}}),
        stderr="",
    )
    with patch("subprocess.run", return_value=fake):
        output = SubprocessPylintRunner(rcfile=".pylintrc").run(["apps"])
    assert isinstance(output, RawLintOutput)
    assert output.exit_code == 0


def test_runner_timeout_raises_error() -> None:
    """Un timeout de Pylint lanza ``LintExecutionError``."""
    runner = SubprocessPylintRunner(timeout=1)
    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="pylint", timeout=1),
    ):
        with pytest.raises(LintExecutionError):
            runner.run(["apps"])
