"""Tests de ``apps.core.menu.MenuRegistry`` y ``group_by_section``."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from apps.core.menu import MenuItem, MenuRegistry, group_by_section


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    """Limpia el singleton entre tests para evitar estado residual."""
    MenuRegistry().reset()


def test_register_deduplicates_by_url_name() -> None:
    """Registrar dos veces el mismo ``url_name`` no duplica el item."""
    registry = MenuRegistry()
    item = MenuItem(label="X", url_name="a:b")
    registry.register(item)
    registry.register(item)
    assert len(registry.items_for(SimpleNamespace(has_perm=lambda _: True))) == 1


def test_register_many_inserts_all_items() -> None:
    """``register_many`` agrega todos los items del iterable."""
    registry = MenuRegistry()
    registry.register_many([
        MenuItem(label="A", url_name="a:a"),
        MenuItem(label="B", url_name="a:b"),
    ])
    assert len(registry.items_for(SimpleNamespace(has_perm=lambda _: True))) == 2


def test_items_for_filters_by_permission() -> None:
    """Solo se devuelven items cuyo permiso tiene el usuario."""
    registry = MenuRegistry()
    registry.register(MenuItem(label="Ver", url_name="v:v", permission="x.view"))
    registry.register(MenuItem(label="Accion", url_name="v:a", permission="x.act"))

    def user_with(perm: str) -> bool:
        return perm == "x.view"

    user = SimpleNamespace(has_perm=user_with)
    visible = registry.items_for(user)
    assert len(visible) == 1
    assert visible[0].label == "Ver"


def test_items_for_orders_by_section_then_order() -> None:
    """Items visibles se ordenan por seccion, orden y etiqueta."""
    registry = MenuRegistry()
    registry.register_many([
        MenuItem(label="Z", url_name="a:a", section="B", order=10),
        MenuItem(label="A", url_name="a:b", section="A", order=5),
        MenuItem(label="Y", url_name="a:c", section="A", order=5),
    ]
    )
    visible = registry.items_for(SimpleNamespace(has_perm=lambda _: True))
    assert [item.label for item in visible] == ["A", "Y", "Z"]


def test_group_by_section_groups_and_orders() -> None:
    """``group_by_section`` agrupa preservando el orden de la lista."""
    items = [
        MenuItem(label="A1", url_name="a:a1", order=1),
        MenuItem(label="A2", url_name="a:a2", order=2),
        MenuItem(label="B1", url_name="b:b1", order=1, section="B"),
    ]
    groups = group_by_section(items)
    assert [g.section for g in groups] == ["General", "B"]
    assert [i.label for i in groups[0].items] == ["A1", "A2"]
    assert [i.label for i in groups[1].items] == ["B1"]
