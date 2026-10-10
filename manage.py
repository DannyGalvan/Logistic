#!/usr/bin/env python
"""Punto de entrada CLI de Django para StockFlow.

Configura la variable de entorno ``DJANGO_SETTINGS_MODULE`` y delega el resto
a :func:`django.core.management.execute_from_command_line`. Mantener este
archivo minimo evita duplicar logica entre la linea de comandos y
``gunicorn config.wsgi``.
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    """Ejecuta un comando de administracion de Django.

    Raises:
        SystemExit: Si Django emite un codigo de salida no nulo.
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        # Import diferido: da un mensaje claro si el venv no esta activo.
        from django.core.management import (  # pylint: disable=import-outside-toplevel
            execute_from_command_line,
        )
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. Activa el entorno virtual e instala "
            "las dependencias con 'uv pip install -r requirements/dev.txt'."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
