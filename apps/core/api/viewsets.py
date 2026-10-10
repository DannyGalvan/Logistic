"""ViewSets base que delegan la escritura en services.

``ServiceModelViewSet`` mantiene los serializers como capa de entrada y
salida: ``perform_create``/``perform_update`` llaman a los services de
la app (via ``create_service``/``update_service``) y el borrado es una
desactivacion logica (``is_active=False``) para no perder historial.
"""

from __future__ import annotations

from typing import Any, Callable

from django.core.exceptions import ImproperlyConfigured
from rest_framework import mixins, viewsets

from .permissions import ModelPermissions


def _service_not_configured(*args: Any, **kwargs: Any) -> Any:
    """Valor por defecto de ``create_service``/``update_service``."""
    raise ImproperlyConfigured("El ViewSet no declara su service de escritura.")


class BaseReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura con permisos por modelo."""

    permission_classes = [ModelPermissions]
    action_permissions: dict[str, list[str]] = {}


class ServiceModelViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    BaseReadOnlyViewSet,
):
    """CRUD cuya escritura pasa por services.

    Atributos:
        create_service: ``f(**data) -> instancia``.
        update_service: ``f(instancia, **data) -> instancia``.
        service_accepts_user: si los services reciben ``user=``.
    """

    create_service: Callable[..., Any] = _service_not_configured
    update_service: Callable[..., Any] = _service_not_configured
    service_accepts_user = True

    def _user_kwargs(self) -> dict[str, Any]:
        """``{"user": request.user}`` si el service lo acepta."""
        return {"user": self.request.user} if self.service_accepts_user else {}

    def perform_create(self, serializer) -> None:  # type: ignore[no-untyped-def]
        """Crea via service y deja la instancia en el serializer."""
        service = type(self).create_service
        serializer.instance = service(**serializer.validated_data, **self._user_kwargs())

    def perform_update(self, serializer) -> None:  # type: ignore[no-untyped-def]
        """Actualiza via service."""
        service = type(self).update_service
        serializer.instance = service(
            serializer.instance, **serializer.validated_data, **self._user_kwargs()
        )

    def perform_destroy(self, instance) -> None:  # type: ignore[no-untyped-def]
        """Desactivacion logica en lugar de borrado fisico."""
        instance.is_active = False
        instance.save(update_fields=["is_active"])


__all__ = ["BaseReadOnlyViewSet", "ServiceModelViewSet"]
