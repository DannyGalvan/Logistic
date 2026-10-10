"""Demuestra ``wrong-import-order``."""

from __future__ import annotations

import sys

from django.db import models  # third-party antes que stdlib -> warning


def hello():
    return sys.path
