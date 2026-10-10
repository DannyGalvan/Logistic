"""Crea grupos y permisos por rol de forma idempotente.

Uso::

    python manage.py setup_roles

Crea un ``Group`` por cada ``Role`` con los permisos declarados en
``accounts.roles.ROLE_PERMISSIONS``. Si un grupo ya existe, reemplaza
su lista de permisos. No asigna usuarios: use ``seed_demo`` para
crear usuarios demo con rol.
"""

from __future__ import annotations

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.roles import ROLE_PERMISSIONS, Role


class Command(BaseCommand):
    """Sincroniza grupos y permisos por rol."""

    help = "Crea/actualiza los grupos y permisos por rol."

    @transaction.atomic
    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        """Aplica los cambios en una sola transaccion."""
        created_count = 0
        updated_count = 0
        for role in Role:
            group, created = Group.objects.get_or_create(name=str(role))
            target_codenames = set(ROLE_PERMISSIONS[role])
            existing = set(
                group.permissions.values_list("codename", flat=True)
            )
            if not created and existing == target_codenames:
                continue
            perms = list(
                Permission.objects.filter(
                    content_type__app_label__in=[
                        code.split(".", 1)[0] for code in target_codenames
                    ],
                    codename__in=[
                        code.split(".", 1)[1] for code in target_codenames
                    ],
                )
            )
            assigned_full = {
                f"{p.content_type.app_label}.{p.codename}" for p in perms
            }
            missing = target_codenames - assigned_full
            if missing:
                self.stdout.write(
                    self.style.WARNING(
                        f"Permisos no encontrados para rol {role}: {missing}"
                    )
                )
            group.permissions.set(perms)
            if created:
                created_count += 1
            else:
                updated_count += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Grupos creados: {created_count}; actualizados: {updated_count}."
            )
        )
