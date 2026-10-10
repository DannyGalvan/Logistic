"""Servicios de ``accounts``.

``assign_role`` es el unico punto que sincroniza el campo ``role`` del
usuario con su ``Group`` de permisos. Lo usan las vistas de usuarios,
``seed_demo`` y las fixtures de pruebas.
"""

from __future__ import annotations

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import transaction

from .models import User
from .roles import Role


@transaction.atomic
def assign_role(user: User, role: Role | str | None) -> User:
    """Asigna ``role`` al usuario y deja ``Group`` como unico grupo.

    Si el grupo aun no existe se ejecuta ``setup_roles``. Un rol vacio
    quita todos los grupos del usuario.
    """
    if not role:
        user.role = ""
        user.save(update_fields=["role"])
        user.groups.clear()
        return user
    role = Role(role)
    group = Group.objects.filter(name=str(role)).first()
    if group is None:
        call_command("setup_roles", verbosity=0)
        group = Group.objects.get(name=str(role))
    user.role = str(role)
    user.save(update_fields=["role"])
    user.groups.set([group])
    return user


__all__ = ["assign_role"]
