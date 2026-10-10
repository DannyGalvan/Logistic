"""Comando ``run_pylint``.

Ejecuta Pylint sobre los targets configurados, persiste la corrida
y devuelve codigo de salida ``0`` cuando la nota alcanza el umbral
configurado en ``PYLINT_FAIL_UNDER`` (default 9.5).
"""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.quality.services import LintService


class Command(BaseCommand):
    """Ejecuta Pylint y persiste la corrida."""

    help = "Ejecuta Pylint y guarda el resultado en BD."

    def add_arguments(self, parser):  # type: ignore[no-untyped-def]
        """Argumentos CLI."""
        parser.add_argument(
            "--targets",
            nargs="*",
            default=list(getattr(settings, "PYLINT_TARGETS", ["apps", "config"])),
        )
        parser.add_argument(
            "--fail-under",
            type=float,
            default=float(getattr(settings, "PYLINT_FAIL_UNDER", 9.5)),
        )

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        """Ejecuta el servicio."""
        service = LintService()
        try:
            run = service.run_project(
                targets=options["targets"],
                user=None,
                source="CLI",
            )
        except Exception as exc:
            raise CommandError(f"Error ejecutando Pylint: {exc}") from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Corrida {run.pk}: nota={run.score} "
                f"({run.convention_count} C / "
                f"{run.refactor_count} R / "
                f"{run.warning_count} W / "
                f"{run.error_count} E / "
                f"{run.fatal_count} F)"
            )
        )
        threshold = options["fail_under"]
        if run.score is not None and float(run.score) < threshold:
            raise CommandError(
                f"Nota {run.score} por debajo del umbral {threshold}."
            )
