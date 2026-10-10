"""Registro de elementos de menu (patron Registry)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class MenuItem:
    """Item estatico del menu lateral.

    Atributos:
        label: Etiqueta visible para el usuario.
        url_name: Nombre de URL (``namespace:name``) resuelto por Django.
        icon: Clase CSS del icono (Bootstrap Icons).
        permission: Codename requerido para mostrar el item o ``None``
            para hacerlo siempre visible.
        order: Orden dentro de su seccion (menor aparece antes).
        section: Seccion logica a la que pertenece.
    """

    label: str
    url_name: str
    icon: str = "bi-circle"
    permission: str | None = None
    order: int = 100
    section: str = "General"


class MenuRegistry:
    """Registro singleton de items del menu.

    Las apps registran sus items en ``AppConfig.ready()`` y la vista
    consume ``items_for(user)`` para renderizar el sidebar respetando
    permisos.
    """

    _instance: "MenuRegistry | None" = None

    def __new__(cls) -> "MenuRegistry":
        """Implementa el patron singleton de forma controlada."""
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._items = []
            cls._instance = instance
        return cls._instance

    def register(self, item: MenuItem) -> None:
        """Registra un item de menu evitando duplicados por ``url_name``."""
        if any(existing.url_name == item.url_name for existing in self._items):
            return
        self._items.append(item)

    def register_many(self, items: Iterable[MenuItem]) -> None:
        """Registra varios items en lote."""
        for item in items:
            self.register(item)

    def items_for(self, user) -> list[MenuItem]:
        """Devuelve los items visibles para ``user`` ordenados.

        Args:
            user: Instancia de ``AUTH_USER_MODEL`` o ``AnonymousUser``.

        Returns:
            Lista de ``MenuItem`` filtrada por permiso y agrupada por orden.
        """
        visible: list[MenuItem] = []
        for item in self._items:
            if item.permission is None or user.has_perm(item.permission):
                visible.append(item)
        visible.sort(key=lambda i: (i.section, i.order, i.label))
        return visible

    def reset(self) -> None:
        """Limpia el registro. Solo util en tests."""
        self._items = []


@dataclass
class MenuGroup:
    """Grupo de items renderizados bajo una misma cabecera."""

    section: str
    items: list[MenuItem] = field(default_factory=list)


def group_by_section(items: Iterable[MenuItem]) -> list[MenuGroup]:
    """Agrupa items del menu por seccion preservando el orden.

    Args:
        items: Items ya filtrados por permiso y ordenados.

    Returns:
        Lista de ``MenuGroup`` con al menos un item por grupo.
    """
    groups: list[MenuGroup] = []
    index: dict[str, int] = {}
    for item in items:
        if item.section not in index:
            index[item.section] = len(groups)
            groups.append(MenuGroup(section=item.section))
        groups[index[item.section]].items.append(item)
    return groups
