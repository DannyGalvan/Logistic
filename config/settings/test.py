"""Ajustes para ejecutar la suite de pruebas.

Sobrescribe la base de datos a SQLite en memoria para no tocar el
Postgres remoto durante ``pytest``. Esto cumple con la decision del
proyecto: tests usan SQLite, desarrollo y produccion usan Postgres.
"""

from __future__ import annotations

from .base import *  # noqa: F401,F403
from .base import PASSWORD_HASHERS as _BASE_HASHERS

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher", *_BASE_HASHERS]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

PYLINT_TIMEOUT = 60
