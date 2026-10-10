"""Ajustes para entorno de desarrollo."""

from __future__ import annotations

import os
import socket

from .base import *  # noqa: F401,F403
from .base import INSTALLED_APPS, MIDDLEWARE

DEBUG = True

INSTALLED_APPS = [*INSTALLED_APPS, "debug_toolbar"]

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]

INTERNAL_IPS = ["127.0.0.1"]
if os.getenv("DOCKER_DEBUG") == "1":
    # En Docker las peticiones llegan desde el gateway de la red bridge
    # (x.x.x.1): se agrega para que se muestre la debug toolbar.
    _, _, _ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [ip[: ip.rfind(".")] + ".1" for ip in _ips]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

LOGGING["loggers"] = {  # noqa: F405
    **LOGGING.get("loggers", {}),  # noqa: F405
    "apps": {"level": "DEBUG", "handlers": ["console"], "propagate": False},
}
