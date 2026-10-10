"""Modelo ``AuditLog`` para bitacora de cambios."""

from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from django.db import models


class AuditLog(models.Model):
    """Bitacora inmutable de cambios y eventos de autenticacion."""

    class Action(models.TextChoices):
        """Tipo de accion auditada."""

        CREATE = "CREATE", "Crear"
        UPDATE = "UPDATE", "Modificar"
        DELETE = "DELETE", "Eliminar"
        LOGIN = "LOGIN", "Inicio sesion"
        LOGOUT = "LOGOUT", "Cierre sesion"
        LOGIN_FAILED = "LOGIN_FAILED", "Login fallido"

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    object_id = models.CharField(max_length=64, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Bitacora"
        verbose_name_plural = "Bitacoras"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        """Devuelve ``usuario accion: object_repr``."""
        actor = self.user.get_username() if self.user else "anon"
        return f"{actor} {self.action}: {self.object_repr}"


__all__ = ["AuditLog"]
