#!/bin/sh
# Punto de entrada del contenedor.
# DJANGO_MIGRATE=1 (default) aplica migraciones antes de arrancar.
set -e

if [ "${DJANGO_MIGRATE:-1}" = "1" ]; then
    python manage.py migrate --noinput
fi

exec "$@"
