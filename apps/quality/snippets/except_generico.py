"""Demuestra ``broad-exception-caught``."""

from __future__ import annotations


def divide(a, b):  # pylint: disable=invalid-name
    try:
        return a / b
    except Exception:
        return None
