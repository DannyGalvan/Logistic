"""Ajustes para ejecutar la suite de pruebas.

Por defecto usa SQLite en memoria para no tocar el Postgres remoto
durante ``pytest``. Con ``TEST_DATABASE_ENGINE=postgres`` usa
``DATABASE_URL`` (la CI levanta su propio ``postgres:16``).
"""

from __future__ import annotations

import os

from .base import *  # noqa: F401,F403
from .base import DATABASES as _BASE_DATABASES
from .base import PASSWORD_HASHERS as _BASE_HASHERS

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher", *_BASE_HASHERS]

_SQLITE_MEMORY = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DATABASES = (
    _BASE_DATABASES if os.getenv("TEST_DATABASE_ENGINE") == "postgres" else _SQLITE_MEMORY
)

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

PYLINT_TIMEOUT = 60
