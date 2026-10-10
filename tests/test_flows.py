"""Flujos end-to-end desde la UI web: compras, ventas, conteos y kardex.

Cada test usa el cliente del rol que opera el paso, igual que en la
verificacion final del plan (seccion 15).
"""

from __future__ import annotations

import datetime
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.roles import Role
from apps.inventory.models import CycleCount, Stock, StockMovement
from apps.inventory.selectors import stock_on_hand
from apps.inventory.services import CycleCountService, InventoryService
from apps.partners.services import create_customer, create_supplier
from apps.purchasing.models import PurchaseOrder
from apps.purchasing.services import PurchaseService
from apps.sales.models import SalesOrder
from apps.sales.services import SalesService

pytestmark = pytest.mark.django_db


@pytest.fixture
def storage(warehouse_with_locations):
    """Ubicacion de almacenamiento ``ALM-01`` del almacen de prueba."""
    return warehouse_with_locations.locations.get(code="ALM-01")


def _messages(response) -> list[str]:
    """Textos de ``django.contrib.messages`` en la respuesta."""
    return [str(m) for m in response.context["messages"]]


def test_purchase_order_full_flow(
    client_as, warehouse_with_locations, storage, product_factory,
) -> None:
    """OC: crear -> linea -> confirmar -> recepcion parcial -> total."""
    product = product_factory()
    supplier = create_supplier(name="Prov", tax_id="P-1")
    buyer = client_as(Role.PURCHASING)
    response = buyer.post(reverse("purchasing:order-create"), {
        "supplier": supplier.pk,
        "warehouse": warehouse_with_locations.pk,
        "order_date": datetime.date.today().isoformat(),
    })
    order = PurchaseOrder.objects.get()
    assert response.url == order.get_absolute_url()

    buyer.post(reverse("purchasing:order-add-line", args=[order.pk]), {
        "product": product.pk, "quantity": "10", "unit_cost": "4",
    })
    buyer.post(reverse("purchasing:order-confirm", args=[order.pk]))
    order.refresh_from_db()
    assert order.status == "CONFIRMED"

    keeper = client_as(Role.WAREHOUSE)
    line = order.lines.get()
    receive_url = reverse("purchasing:order-receive", args=[order.pk])
    keeper.post(receive_url, {"location": storage.pk, f"qty_{line.pk}": "4"})
    order.refresh_from_db()
    assert order.status == "PARTIALLY_RECEIVED"
    keeper.post(receive_url, {"location": storage.pk, f"qty_{line.pk}": "6"})
    order.refresh_from_db()
    assert order.status == "RECEIVED"
    assert stock_on_hand(product) == Decimal("10")
    detail = keeper.get(order.get_absolute_url())
    assert detail.status_code == 200
    assert detail.context["receipts"].count() == 2


def test_purchase_receive_errors_are_messages(
    client_as, warehouse_with_locations, storage, product_factory, users_by_role,
) -> None:
    """Recibir mas de lo pendiente muestra un error y no cambia el stock."""
    product = product_factory()
    service = PurchaseService()
    order = service.create_order(
        supplier=create_supplier(name="Prov", tax_id="P-2"),
        warehouse=warehouse_with_locations,
        order_date=datetime.date.today(),
        user=users_by_role[Role.PURCHASING],
    )
    line = service.add_line(
        order, product=product, quantity=Decimal("2"), unit_cost=Decimal("1"),
    )
    service.confirm(order)
    response = client_as(Role.WAREHOUSE).post(
        reverse("purchasing:order-receive", args=[order.pk]),
        {"location": storage.pk, f"qty_{line.pk}": "5"},
        follow=True,
    )
    assert any("excede" in text for text in _messages(response))
    assert stock_on_hand(product) == Decimal("0")


def test_purchase_confirm_forbidden_for_viewer(
    client_as, warehouse_with_locations,
) -> None:
    """El rol Consulta recibe 403 al intentar confirmar."""
    order = PurchaseOrder.objects.create(
        code="OC-X", supplier=create_supplier(name="S", tax_id="P-3"),
        warehouse=warehouse_with_locations, order_date=datetime.date.today(),
    )
    response = client_as(Role.VIEWER).post(
        reverse("purchasing:order-confirm", args=[order.pk])
    )
    assert response.status_code == 403


def test_sales_order_full_flow(
    client_as, warehouse_with_locations, storage, product_factory, users_by_role,
) -> None:
    """OV: crear -> linea -> confirmar -> picking FEFO -> despacho."""
    product = product_factory(track_lots=True, track_expiry=True,
                              rotation_strategy="FEFO")
    _receive_two_lots(product, storage, users_by_role[Role.WAREHOUSE])
    today = datetime.date.today()
    seller = client_as(Role.SALES)
    seller.post(reverse("sales:order-create"), {
        "customer": create_customer(name="Cli", tax_id="C-1").pk,
        "warehouse": warehouse_with_locations.pk,
        "order_date": today.isoformat(),
    })
    order = SalesOrder.objects.get()
    seller.post(reverse("sales:order-add-line", args=[order.pk]), {
        "product": product.pk, "quantity": "3", "unit_price": "9",
    })
    seller.post(reverse("sales:order-confirm", args=[order.pk]))

    keeper = client_as(Role.WAREHOUSE)
    detail = keeper.get(order.get_absolute_url())
    picking = detail.context["picking"]
    assert [row["lot"].lot_number for row in picking] == ["EARLY"]
    row = picking[0]
    keeper.post(reverse("sales:order-ship", args=[order.pk]), {
        "row": ["1"],
        "line_1": row["order_line_id"],
        "location_1": row["location_id"],
        "lot_1": row["lot_id"],
        "qty_1": "3",
        "carrier": "Propio",
    })
    order.refresh_from_db()
    assert order.status == "SHIPPED"
    early = Stock.objects.get(product=product, lot__lot_number="EARLY")
    assert early.quantity == Decimal("2")


def _receive_two_lots(product, location, user) -> None:
    """Recibe un lote que vence tarde y otro que vence pronto."""
    today = datetime.date.today()
    for lot_number, days in (("LATE", 200), ("EARLY", 20)):
        InventoryService().receive(
            product=product, location=location, quantity=Decimal("5"),
            unit_cost=Decimal("1"), user=user,
            lot_number=lot_number, expires_at=today + datetime.timedelta(days=days),
        )


def test_sales_picking_reports_insufficient_stock(
    client_as, warehouse_with_locations, product_factory, users_by_role,
) -> None:
    """Sin stock el detalle muestra el error de picking en vez de un 500."""
    product = product_factory()
    service = SalesService()
    order = service.create_order(
        customer=create_customer(name="Cli", tax_id="C-2"),
        warehouse=warehouse_with_locations,
        order_date=datetime.date.today(),
        user=users_by_role[Role.SALES],
    )
    service.add_line(order, product=product, quantity=Decimal("1"),
                     unit_price=Decimal("1"))
    service.confirm(order)
    response = client_as(Role.WAREHOUSE).get(order.get_absolute_url())
    assert response.status_code == 200
    assert response.context["picking_error"]


def test_cycle_count_flow_generates_adjustment(
    client_as, warehouse_with_locations, storage, product_factory, users_by_role,
) -> None:
    """Conteo: crear -> iniciar -> registrar -> aprobar genera ajuste."""
    product = product_factory()
    InventoryService().receive(
        product=product, location=storage, quantity=Decimal("10"),
        unit_cost=Decimal("1"), user=users_by_role[Role.WAREHOUSE],
    )
    keeper = client_as(Role.WAREHOUSE)
    keeper.post(reverse("inventory:cycle-count-create"), {
        "warehouse": warehouse_with_locations.pk,
    })
    cycle = CycleCount.objects.get()
    keeper.post(reverse("inventory:cycle-count-start", args=[cycle.pk]))
    line = cycle.lines.get()
    keeper.post(reverse("inventory:cycle-count-record", args=[cycle.pk]),
                {f"count_{line.pk}": "7"})
    forbidden = keeper.post(
        reverse("inventory:cycle-count-approve", args=[cycle.pk])
    )
    assert forbidden.status_code == 403

    client_as(Role.SUPERVISOR).post(
        reverse("inventory:cycle-count-approve", args=[cycle.pk])
    )
    cycle.refresh_from_db()
    assert cycle.status == "APPROVED"
    assert stock_on_hand(product) == Decimal("7")
    assert StockMovement.objects.filter(movement_type="ADJUSTMENT_OUT").exists()


def test_cycle_count_approve_requires_all_lines(
    client_as, warehouse_with_locations, storage, product_factory, users_by_role,
) -> None:
    """Aprobar sin capturar todas las lineas muestra un error."""
    product = product_factory()
    user = users_by_role[Role.SUPERVISOR]
    InventoryService().receive(
        product=product, location=storage, quantity=Decimal("1"),
        unit_cost=Decimal("1"), user=user,
    )
    service = CycleCountService()
    cycle = service.create(warehouse=warehouse_with_locations, user=user)
    service.start(cycle)
    response = client_as(Role.SUPERVISOR).post(
        reverse("inventory:cycle-count-approve", args=[cycle.pk]), follow=True,
    )
    assert any("contadas" in text for text in _messages(response))
    cycle.refresh_from_db()
    assert cycle.status == "IN_PROGRESS"


def test_kardex_view_shows_running_balance(
    client_as, warehouse_with_locations, storage, product_factory, users_by_role,
) -> None:
    """El kardex muestra entradas, salidas y saldo acumulado."""
    product = product_factory()
    user = users_by_role[Role.WAREHOUSE]
    inventory = InventoryService()
    inventory.receive(product=product, location=storage, quantity=Decimal("8"),
                      unit_cost=Decimal("2"), user=user)
    inventory.issue(product=product, location=storage, quantity=Decimal("3"),
                    user=user)
    other = warehouse_with_locations.locations.get(code="DES")
    inventory.transfer(product=product, from_location=storage, to_location=other,
                       quantity=Decimal("1"), user=user)
    response = client_as(Role.VIEWER).get(
        reverse("inventory:kardex"), {"product": product.pk}
    )
    assert response.status_code == 200
    balances = [row.balance for row in response.context["rows"]]
    assert balances == [Decimal("8"), Decimal("5"), Decimal("5")]
