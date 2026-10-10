"""Comando ``generate_uml``.

Genera diagramas de clases y paquetes con ``pyreverse`` (incluido en
Pylint) para cada app del proyecto. Por defecto produce Mermaid
(``.mmd``), que no requiere Graphviz; con ``--format png`` o ``svg`` se
necesita el binario ``dot`` de Graphviz.

Uso::

    python manage.py generate_uml [--format mmd|puml|dot|png|svg] [--apps inventory sales]
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

DEFAULT_APPS = [
    "core", "accounts", "catalog", "warehouses", "partners", "inventory",
    "purchasing", "sales", "reports", "audit", "quality",
]
TEXT_FORMATS = {"mmd", "puml", "dot", "html"}


class Command(BaseCommand):
    """Genera diagramas UML con ``pyreverse``."""

    help = "Genera diagramas UML (clases y paquetes) en docs/uml/."

    def add_arguments(self, parser):  # type: ignore[no-untyped-def]
        """Argumentos CLI."""
        parser.add_argument("--format", default="mmd", help="mmd, puml, dot, png, svg...")
        parser.add_argument("--apps", nargs="*", default=DEFAULT_APPS)
        parser.add_argument(
            "--output", default=str(Path(settings.BASE_DIR) / "docs" / "uml"),
            help="Directorio de salida.",
        )

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        """Ejecuta ``pyreverse`` una vez por app."""
        fmt = options["format"]
        if fmt not in TEXT_FORMATS and shutil.which("dot") is None:
            raise CommandError(
                f"El formato '{fmt}' requiere Graphviz (dot). Usa --format mmd o instala graphviz."
            )
        output = Path(options["output"])
        output.mkdir(parents=True, exist_ok=True)
        for app in options["apps"]:
            command = [
                sys.executable, "-m", "pylint.pyreverse.main",
                "-o", fmt, "-p", app, "-d", str(output),
                "--ignore", "migrations,tests,snippets",
                f"apps.{app}",
            ]
            completed = subprocess.run(
                command, cwd=settings.BASE_DIR, capture_output=True, text=True,
                check=False, timeout=180,
            )
            if completed.returncode != 0:
                raise CommandError(f"pyreverse fallo en {app}: {completed.stderr.strip()}")
            self.stdout.write(f"  - {app}: classes_{app}.{fmt}, packages_{app}.{fmt}")
        self.stdout.write(self.style.SUCCESS(f"Diagramas generados en {output}"))
