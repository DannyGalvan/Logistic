"""Roles de StockFlow y matriz de permisos por rol.

Cada rol tiene un nombre legible y una lista de ``app_label.codename``
que Django aplica via ``Group.permissions``. La lista de permisos
custom se mantiene en ``apps/accounts/models.py:CustomPermissions``
para que las migraciones de accounts no dependan de apps aun no
implementadas.
"""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    """Roles de StockFlow.

    El valor es el codename del ``Group`` correspondiente en la BD.
    """

    ADMIN = "Administrador"
    SUPERVISOR = "Supervisor"
    WAREHOUSE = "Almacenista"
    PURCHASING = "Compras"
    SALES = "Ventas"
    VIEWER = "Consulta"


# Codenames puros (sin prefijo ``app_label.``). El prefijo se aplica
# en ``ROLE_PERMISSIONS`` segun el ``app_label`` declarado.
PERMISSIONS_BY_APP: dict[str, list[str]] = {
    "accounts": [
        "view_user",
        "add_user",
        "change_user",
        "delete_user",
    ],
    "catalog": [
        "view_product",
        "add_product",
        "change_product",
        "view_category",
        "view_brand",
        "view_unitofmeasure",
    ],
    "warehouses": [
        "view_warehouse",
        "add_warehouse",
        "change_warehouse",
        "view_location",
        "add_location",
        "change_location",
    ],
    "partners": [
        "view_supplier",
        "add_supplier",
        "change_supplier",
        "view_customer",
        "add_customer",
        "change_customer",
    ],
    "inventory": [
        "view_stock",
        "view_movement",
        "add_stockmovement",
        "add_cyclecount",
        "view_cyclecount",
        "view_alert",
    ],
    "purchasing": [
        "view_purchaseorder",
        "add_purchaseorder",
        "change_purchaseorder",
        "view_goodsreceipt",
        "add_goodsreceipt",
    ],
    "sales": [
        "view_salesorder",
        "add_salesorder",
        "change_salesorder",
        "view_shipment",
        "add_shipment",
    ],
    "reports": [
        "view_reports",
    ],
    "audit": [
        "view_auditlog",
    ],
    "quality": [
        "view_lintrun",
        "view_lintmessagerecord",
    ],
}


def _prefix(app: str) -> list[str]:
    """Devuelve ``[app.codename, ...]`` para una app del dict."""
    return [f"{app}.{codename}" for codename in PERMISSIONS_BY_APP[app]]


ROLE_PERMISSIONS: dict[Role, list[str]] = {
    Role.ADMIN: [perm for app in PERMISSIONS_BY_APP for perm in _prefix(app)],
    Role.SUPERVISOR: [
        *_prefix("catalog"),
        "catalog.change_product",
        *_prefix("warehouses"),
        "warehouses.change_warehouse",
        *_prefix("partners"),
        "partners.change_supplier",
        "partners.change_customer",
        "inventory.view_stock",
        "inventory.view_movement",
        "inventory.add_stockmovement",
        "inventory.add_cyclecount",
        "inventory.view_cyclecount",
        "inventory.approve_cyclecount",
        "inventory.view_kardex",
        "inventory.view_alert",
        "purchasing.view_purchaseorder",
        "purchasing.change_purchaseorder",
        "purchasing.confirm_purchaseorder",
        "purchasing.receive_purchaseorder",
        "purchasing.view_goodsreceipt",
        "sales.view_salesorder",
        "sales.change_salesorder",
        "sales.confirm_salesorder",
        "sales.ship_salesorder",
        "sales.view_shipment",
        "reports.view_reports",
        "audit.view_auditlog",
        "quality.view_lintrun",
        "quality.run_lint",
    ],
    Role.WAREHOUSE: [
        "catalog.view_product",
        "warehouses.view_warehouse",
        "warehouses.view_location",
        "inventory.view_stock",
        "inventory.view_movement",
        "inventory.add_stockmovement",
        "inventory.add_cyclecount",
        "inventory.view_cyclecount",
        "inventory.view_kardex",
        "inventory.view_alert",
        "purchasing.view_purchaseorder",
        "purchasing.receive_purchaseorder",
        "purchasing.view_goodsreceipt",
        "purchasing.add_goodsreceipt",
        "sales.view_salesorder",
        "sales.ship_salesorder",
        "sales.view_shipment",
        "reports.view_reports",
        "quality.view_lintrun",
    ],
    Role.PURCHASING: [
        "catalog.view_product",
        "warehouses.view_warehouse",
        "partners.view_supplier",
        "partners.add_supplier",
        "partners.change_supplier",
        "inventory.view_stock",
        "inventory.view_movement",
        "inventory.view_kardex",
        "purchasing.view_purchaseorder",
        "purchasing.add_purchaseorder",
        "purchasing.change_purchaseorder",
        "purchasing.confirm_purchaseorder",
        "purchasing.view_goodsreceipt",
        "reports.view_reports",
        "quality.view_lintrun",
    ],
    Role.SALES: [
        "catalog.view_product",
        "warehouses.view_warehouse",
        "partners.view_customer",
        "partners.add_customer",
        "partners.change_customer",
        "inventory.view_stock",
        "inventory.view_movement",
        "inventory.view_kardex",
        "sales.view_salesorder",
        "sales.add_salesorder",
        "sales.change_salesorder",
        "sales.confirm_salesorder",
        "sales.view_shipment",
        "reports.view_reports",
        "quality.view_lintrun",
    ],
    Role.VIEWER: [
        "catalog.view_product",
        "warehouses.view_warehouse",
        "warehouses.view_location",
        "partners.view_supplier",
        "partners.view_customer",
        "inventory.view_stock",
        "inventory.view_movement",
        "inventory.view_kardex",
        "inventory.view_cyclecount",
        "purchasing.view_purchaseorder",
        "purchasing.view_goodsreceipt",
        "sales.view_salesorder",
        "sales.view_shipment",
        "reports.view_reports",
        "quality.view_lintrun",
    ],
}


CUSTOM_PERMISSIONS: list[tuple[str, str]] = [
    ("approve_cyclecount", "Puede aprobar conteos ciclicos"),
    ("view_kardex", "Puede consultar el Kardex valorizado"),
    ("confirm_purchaseorder", "Puede confirmar ordenes de compra"),
    ("receive_purchaseorder", "Puede recepcionar ordenes de compra"),
    ("confirm_salesorder", "Puede confirmar ordenes de venta"),
    ("ship_salesorder", "Puede despachar ordenes de venta"),
    ("run_lint", "Puede ejecutar Pylint desde la app"),
    ("view_auditlog", "Puede consultar la bitacora de auditoria"),
    ("view_reports", "Puede consultar reportes y dashboard"),
]


__all__ = [
    "Role",
    "ROLE_PERMISSIONS",
    "CUSTOM_PERMISSIONS",
    "PERMISSIONS_BY_APP",
]
