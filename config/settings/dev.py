"""Ajustes para entorno de desarrollo."""

from __future__ import annotations

from .base import *  # noqa: F401,F403
from .base import INSTALLED_APPS, MIDDLEWARE

DEBUG = True

INSTALLED_APPS = [*INSTALLED_APPS, "debug_toolbar"]

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]

INTERNAL_IPS = ["127.0.0.1"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

LOGGING["root"]["level"] = "DEBUG"
