"""Ajustes para entorno de produccion.

Lee ``SECURE_*`` y ``SESSION_COOKIE_SECURE`` desde ``.env``. No usar en
desarrollo: el ``SecurityMiddleware`` rechaza cookies no seguras en HTTP.
"""

from __future__ import annotations

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import STORAGES

DEBUG = False

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("DJANGO_SECURE_SSL_REDIRECT", "1") != "0"
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_BROWSER_XSS_FILTER = True
# Solo para probar el contenedor en http://localhost: DJANGO_SECURE_COOKIES=0.
SESSION_COOKIE_SECURE = os.getenv("DJANGO_SECURE_COOKIES", "1") != "0"
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE

STORAGES = {
    **STORAGES,
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

if not ALLOWED_HOSTS:  # noqa: F405
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS es obligatorio en produccion.")

if SECRET_KEY.startswith("insecure-"):  # noqa: F405
    raise ImproperlyConfigured("Define DJANGO_SECRET_KEY para produccion.")
