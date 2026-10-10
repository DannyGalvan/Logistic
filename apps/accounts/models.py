"""Modelos de la app ``accounts``.

En la Fase 2 se reemplaza este archivo por el modelo ``User`` real.
Por ahora exponemos un marcador para que ``makemigrations`` no falle.
"""

from __future__ import annotations

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Usuario placeholder de Fase 1."""

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self) -> str:
        """Devuelve el username como representacion legible."""
        return self.username


__all__ = ["User"]
