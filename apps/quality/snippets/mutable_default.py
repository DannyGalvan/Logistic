"""Demuestra ``dangerous-default-value``."""

from __future__ import annotations


def add(item, bag=[]):  # pylint: disable=invalid-name
    bag.append(item)
    return bag
