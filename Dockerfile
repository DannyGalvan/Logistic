# syntax=docker/dockerfile:1.7
# StockFlow - imagen multi-stage.
#   target "prod" (default): gunicorn, solo dependencias de produccion.
#   target "dev": dependencias de desarrollo + graphviz + debugpy (perfil debug).

FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements/ requirements/
RUN pip install -r requirements/prod.txt
RUN groupadd --system app && useradd --system --gid app --home /app app

FROM base AS dev
RUN apt-get update \
    && apt-get install -y --no-install-recommends graphviz \
    && rm -rf /var/lib/apt/lists/*
RUN pip install -r requirements/dev.txt
COPY --chown=app:app . .
USER app
ENTRYPOINT ["scripts/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS prod
ENV DJANGO_SETTINGS_MODULE=config.settings.prod
COPY --chown=app:app . .
# collectstatic no necesita BD ni secretos reales.
RUN DJANGO_SECRET_KEY=build-only-collectstatic DJANGO_ALLOWED_HOSTS=localhost \
    DATABASE_URL=sqlite:////tmp/build.sqlite3 \
    python manage.py collectstatic --noinput \
    && chown -R app:app /app
USER app
EXPOSE 8000
ENTRYPOINT ["scripts/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "-b", "0.0.0.0:8000", "-w", "3", "--access-logfile", "-"]
