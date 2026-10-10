"""Ajustes base compartidos por todos los entornos.

Carga variables desde ``.env`` (si existe) mediante ``django-environ`` y
declara apps, middlewares y resto de parametros comunes. Ninguna clave
real debe vivir en el codigo: use ``.env`` (gitignored) para inyectarlas.
"""

from __future__ import annotations

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    DB_CONN_MAX_AGE=(int, 60),
    PYLINT_TARGETS=(list, ["apps", "config"]),
    PYLINT_FAIL_UNDER=(float, 9.5),
    PYLINT_TIMEOUT=(int, 180),
    PYLINT_SNIPPET_MAX_BYTES=(int, 20000),
    EXPIRY_ALERT_DAYS=(int, 30),
    TEST_DATABASE_NAME=(str, "test_logistic"),
)

env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="insecure-dev-key-do-not-use-in-production",
)
DEBUG = env("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default="http://localhost:8000",
)
if isinstance(CSRF_TRUSTED_ORIGINS, str):
    CSRF_TRUSTED_ORIGINS = [origin for origin in CSRF_TRUSTED_ORIGINS.split(",") if origin]

AUTH_USER_MODEL = "accounts.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "django_filters",
    "django_htmx",
    "crispy_forms",
    "crispy_bootstrap5",
    "apps.core",
    "apps.accounts",
    "apps.catalog",
    "apps.warehouses",
    "apps.partners",
    "apps.inventory",
    "apps.purchasing",
    "apps.sales",
    "apps.reports",
    "apps.audit",
    "apps.quality",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "apps.core.middleware.CurrentUserMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.menu",
                "apps.core.context_processors.alerts_count",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL"),
}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
DATABASES["default"]["TEST"] = {"NAME": env("TEST_DATABASE_NAME", default="test_logistic")}

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Guatemala"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        "rest_framework.permissions.DjangoModelPermissions",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "apps.core.api.exceptions.domain_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "StockFlow API",
    "DESCRIPTION": "API REST del sistema de inventario y logistica StockFlow.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

PYLINT_RCFILE = str(BASE_DIR / ".pylintrc")
PYLINT_TARGETS = env.list("PYLINT_TARGETS", default=["apps", "config"])
PYLINT_FAIL_UNDER = env.float("PYLINT_FAIL_UNDER", default=9.5)
PYLINT_TIMEOUT = env.int("PYLINT_TIMEOUT", default=180)
PYLINT_SNIPPET_MAX_BYTES = env.int("PYLINT_SNIPPET_MAX_BYTES", default=20000)

EXPIRY_ALERT_DAYS = env.int("EXPIRY_ALERT_DAYS", default=30)

# Contrasena de los usuarios demo generados por ``seed_demo``.
# Sobre escribir con ``SEED_DEMO_PASSWORD`` en .env para entornos reales.
SEED_DEMO_PASSWORD = env(
    "SEED_DEMO_PASSWORD",
    default="Cambia-en-produccion-1234",
)

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
