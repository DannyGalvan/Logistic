"""Demuestra ``too-many-arguments``."""

from __future__ import annotations


def funcion_con_muchos_args(
    a, b, c, d, e, f, g, h,
):  # pylint: disable=too-many-arguments,unused-argument
    return a + b + c + d + e + f + g + h
