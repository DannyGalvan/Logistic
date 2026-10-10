"""Permisos DRF compartidos.

- ``ModelPermissions`` extiende ``DjangoModelPermissions`` para exigir
  tambien ``view_<modelo>`` en lecturas (DRF no lo hace por defecto).
- Las acciones custom (``@action``) declaran su permiso en
  ``action_permissions`` del ViewSet; ``ModelPermissions`` lo aplica.
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission, DjangoModelPermissions


class ModelPermissions(DjangoModelPermissions):
    """Permisos por modelo que incluyen lectura y acciones custom."""

    perms_map = {
        **DjangoModelPermissions.perms_map,
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        # DELETE es una desactivacion logica (ver ``ServiceModelViewSet``).
        "DELETE": ["%(app_label)s.change_%(model_name)s"],
    }

    def has_permission(self, request, view) -> bool:  # type: ignore[no-untyped-def]
        """Usa ``action_permissions`` si la accion lo define."""
        if not request.user or not request.user.is_authenticated:
            return False
        action_perms = getattr(view, "action_permissions", {})
        action = getattr(view, "action", None)
        if action in action_perms:
            return request.user.has_perms(action_perms[action])
        return super().has_permission(request, view)


class RequiredPermissions(BasePermission):
    """Exige los permisos listados en ``view.required_permissions``.

    Para vistas sin ``queryset`` (KPIs, endpoints de agregados).
    """

    def has_permission(self, request, view) -> bool:  # type: ignore[no-untyped-def]
        """Usuario autenticado con todos los permisos requeridos."""
        user = request.user
        return bool(
            user and user.is_authenticated
            and user.has_perms(getattr(view, "required_permissions", []))
        )


__all__ = ["ModelPermissions", "RequiredPermissions"]
