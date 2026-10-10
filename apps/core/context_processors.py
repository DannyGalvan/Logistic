"""Context processors inyectados en cada plantilla."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from .menu import group_by_section, MenuRegistry
from .selectors import unread_alerts_count


def menu(request: HttpRequest) -> dict[str, Any]:
    """Inyecta el menu lateral segmentado por permisos."""
    registry = MenuRegistry()
    items = registry.items_for(getattr(request, "user", None))
    return {"menu_groups": group_by_section(items)}


def alerts_count(request: HttpRequest) -> dict[str, Any]:
    """Inyecta el contador de alertas no leidas."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"alerts_count": 0}
    return {"alerts_count": unread_alerts_count()}
