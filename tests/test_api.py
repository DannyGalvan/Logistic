"""Pruebas de la API REST ``/api/v1/`` (plan, seccion 8)."""

from __future__ import annotations

import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.accounts.roles import Role
from apps.inventory.models import CycleCount
from apps.inventory.selectors import stock_on_hand
from apps.inventory.services import InventoryService
from apps.partners.services import create_customer, create_supplier
from apps.quality.models import LintRun

pytestmark = pytest.mark.django_db
API = "/api/v1"


@pytest.fixture
def storage(warehouse_with_locations):
    """Ubicacion ``ALM-01``."""
    return warehouse_with_locations.locations.get(code="ALM-01")


def test_anonymous_is_rejected() -> None:
    """Sin credenciales la API responde 401/403."""
    assert APIClient().get(f"{API}/products/").status_code in (401, 403)


def test_token_auth(users_by_role) -> None:
    """``POST auth/token/`` devuelve un token utilizable."""
    user = users_by_role[Role.VIEWER]
    response = APIClient().post(
        f"{API}/auth/token/", {"username": user.username, "password": "test1234"}
    )
    assert response.status_code == 200
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
    assert client.get(f"{API}/products/").status_code == 200


def test_catalog_crud_and_soft_delete(api_client_as) -> None:
    """Admin crea, edita y desactiva; Consulta solo lee."""
    admin = api_client_as(Role.ADMIN)
    category = admin.post(f"{API}/categories/", {"name": "Bebidas"}).data
    uom = admin.post(f"{API}/uoms/", {"code": "UND", "name": "Unidad"}).data
    created = admin.post(f"{API}/products/", {
        "sku": "API-1", "name": "Agua", "category": category["id"], "uom": uom["id"],
        "sale_price": "3.50",
    })
    assert created.status_code == 201, created.data
    url = f"{API}/products/{created.data['id']}/"
    assert admin.patch(url, {"name": "Agua pura"}).data["name"] == "Agua pura"
    assert admin.delete(url).status_code == 204
    assert admin.get(url).data["is_active"] is False

    viewer = api_client_as(Role.VIEWER)
    assert viewer.get(f"{API}/products/").status_code == 200
    assert viewer.post(f"{API}/brands/", {"name": "X"}).status_code == 403


def test_read_requires_view_permission(api_client_as) -> None:
    """Ventas no ve proveedores: lectura tambien exige permiso."""
    assert api_client_as(Role.SALES).get(f"{API}/suppliers/").status_code == 403
    assert api_client_as(Role.SALES).get(f"{API}/customers/").status_code == 200


def test_master_data_endpoints(api_client_as) -> None:
    """Almacenes (con ubicaciones), ubicaciones y socios."""
    admin = api_client_as(Role.ADMIN)
    warehouse = admin.post(f"{API}/warehouses/", {"code": "API", "name": "Api"})
    assert warehouse.status_code == 201
    assert len(warehouse.data["locations"]) == 4
    location = admin.post(f"{API}/locations/", {
        "warehouse": warehouse.data["id"], "code": "X-1", "name": "Extra",
        "location_type": "STORAGE",
    })
    assert location.status_code == 201, location.data
    assert admin.post(f"{API}/suppliers/", {"name": "S", "tax_id": "S-1"}).status_code == 201
    assert admin.post(f"{API}/customers/", {"name": "C", "tax_id": "C-1"}).status_code == 201


def test_inventory_actions_and_domain_errors(
    api_client_as, storage, product_factory, warehouse_with_locations,
) -> None:
    """receive/issue/transfer/adjust y ``DomainError`` -> 400."""
    product = product_factory()
    keeper = api_client_as(Role.WAREHOUSE)
    response = keeper.post(f"{API}/movements/receive/", {
        "product": product.pk, "location": storage.pk, "quantity": "10", "unit_cost": "2",
    })
    assert response.status_code == 201, response.data
    other = warehouse_with_locations.locations.get(code="DES")
    assert keeper.post(f"{API}/movements/transfer/", {
        "product": product.pk, "from_location": storage.pk, "to_location": other.pk,
        "quantity": "3",
    }).status_code == 201
    assert keeper.post(f"{API}/movements/adjust/", {
        "product": product.pk, "location": storage.pk, "counted_quantity": "6",
    }).status_code == 201
    too_much = keeper.post(f"{API}/movements/issue/", {
        "product": product.pk, "location": storage.pk, "quantity": "100",
    })
    assert too_much.status_code == 400
    assert too_much.data["code"] == "InsufficientStockError"
    assert stock_on_hand(product) == Decimal("9")
    assert keeper.get(f"{API}/stock/", {"product": product.pk}).data["count"] == 2
    kardex = keeper.get(f"{API}/movements/kardex/", {"product": product.pk})
    assert kardex.status_code == 200
    assert kardex.data[-1]["balance"] == "9.000"
    assert keeper.get(f"{API}/lots/").status_code == 200


def test_viewer_cannot_move_stock(api_client_as, storage, product_factory) -> None:
    """Consulta no puede registrar movimientos."""
    response = api_client_as(Role.VIEWER).post(f"{API}/movements/receive/", {
        "product": product_factory().pk, "location": storage.pk,
        "quantity": "1", "unit_cost": "1",
    })
    assert response.status_code == 403


def test_purchase_order_api_flow(
    api_client_as, warehouse_with_locations, storage, product_factory,
) -> None:
    """Crear con lineas -> confirmar -> recibir parcial -> total."""
    product = product_factory()
    buyer = api_client_as(Role.PURCHASING)
    created = buyer.post(f"{API}/purchase-orders/", {
        "supplier": create_supplier(name="S", tax_id="S-9").pk,
        "warehouse": warehouse_with_locations.pk,
        "order_date": datetime.date.today().isoformat(),
        "lines": [{"product": product.pk, "quantity": "5", "unit_cost": "2"}],
    }, format="json")
    assert created.status_code == 201, created.data
    order_url = f"{API}/purchase-orders/{created.data['id']}"
    assert buyer.post(f"{order_url}/lines/", {
        "product": product_factory().pk, "quantity": "1", "unit_cost": "1",
    }).status_code == 201
    assert buyer.post(f"{order_url}/confirm/").data["status"] == "CONFIRMED"
    assert buyer.post(f"{order_url}/receive/", {}).status_code == 403

    keeper = api_client_as(Role.WAREHOUSE)
    line_id = created.data["lines"][0]["id"]
    receipt = keeper.post(f"{order_url}/receive/", {
        "location": storage.pk, "lines": [{"order_line_id": line_id, "quantity": "2"}],
    }, format="json")
    assert receipt.status_code == 201, receipt.data
    over = keeper.post(f"{order_url}/receive/", {
        "location": storage.pk, "lines": [{"order_line_id": line_id, "quantity": "9"}],
    }, format="json")
    assert over.status_code == 400
    assert keeper.get(f"{order_url}/").data["status"] == "PARTIALLY_RECEIVED"
    assert buyer.post(f"{order_url}/cancel/").status_code == 400


def test_sales_order_api_flow(
    api_client_as, warehouse_with_locations, storage, product_factory, users_by_role,
) -> None:
    """Crear -> confirmar -> suggest-picking -> ship."""
    product = product_factory()
    InventoryService().receive(
        product=product, location=storage, quantity=Decimal("8"),
        unit_cost=Decimal("1"), user=users_by_role[Role.WAREHOUSE],
    )
    seller = api_client_as(Role.SALES)
    created = seller.post(f"{API}/sales-orders/", {
        "customer": create_customer(name="C", tax_id="C-9").pk,
        "warehouse": warehouse_with_locations.pk,
        "order_date": datetime.date.today().isoformat(),
        "lines": [{"product": product.pk, "quantity": "3", "unit_price": "7"}],
    }, format="json")
    assert created.status_code == 201, created.data
    order_url = f"{API}/sales-orders/{created.data['id']}"
    seller.post(f"{order_url}/lines/", {
        "product": product.pk, "quantity": "1", "unit_price": "7",
    })
    assert seller.post(f"{order_url}/confirm/").data["status"] == "CONFIRMED"

    keeper = api_client_as(Role.WAREHOUSE)
    picking = keeper.get(f"{order_url}/suggest-picking/")
    assert picking.status_code == 200
    shipment = keeper.post(f"{order_url}/ship/", {"lines": picking.data}, format="json")
    assert shipment.status_code == 201, shipment.data
    assert keeper.get(f"{order_url}/").data["status"] == "SHIPPED"
    assert stock_on_hand(product) == Decimal("4")
    assert seller.post(f"{order_url}/cancel/").status_code == 400


def test_cycle_count_api(
    api_client_as, warehouse_with_locations, storage, product_factory, users_by_role,
) -> None:
    """Crear -> start -> record -> approve (solo supervisor)."""
    product = product_factory()
    InventoryService().receive(
        product=product, location=storage, quantity=Decimal("5"),
        unit_cost=Decimal("1"), user=users_by_role[Role.WAREHOUSE],
    )
    keeper = api_client_as(Role.WAREHOUSE)
    created = keeper.post(f"{API}/cycle-counts/", {"warehouse": warehouse_with_locations.pk})
    assert created.status_code == 201, created.data
    url = f"{API}/cycle-counts/{created.data['id']}"
    assert keeper.post(f"{url}/start/").data["status"] == "IN_PROGRESS"
    line_id = created.data["lines"][0]["id"]
    recorded = keeper.post(f"{url}/record/", {
        "lines": [{"id": line_id, "counted_quantity": "4"}],
    }, format="json")
    assert recorded.data["lines"][0]["difference"] == "-1.000"
    assert keeper.post(f"{url}/approve/").status_code == 403
    approved = api_client_as(Role.SUPERVISOR).post(f"{url}/approve/")
    assert approved.data["status"] == "APPROVED"
    assert stock_on_hand(product) == Decimal("4")
    assert CycleCount.objects.get().approved_by is not None


def test_lint_runs_api(api_client_as) -> None:
    """Lectura de corridas y ``run`` solo con ``accounts.run_lint``."""
    run = LintRun.objects.create(target="apps", score=Decimal("9.80"))
    viewer = api_client_as(Role.VIEWER)
    assert api_client_as(Role.WAREHOUSE).get(f"{API}/lint-runs/{run.pk}/").status_code == 200
    assert viewer.post(f"{API}/lint-runs/run/").status_code == 403
    with patch("apps.quality.services.LintService.run_project", return_value=run) as fake:
        response = api_client_as(Role.SUPERVISOR).post(
            f"{API}/lint-runs/run/", {"targets": ["apps/core"]}, format="json"
        )
    assert response.status_code == 201
    assert fake.call_args.kwargs["targets"] == ["apps/core"]


def test_reports_kpis(api_client_as) -> None:
    """KPIs requieren ``reports.view_reports``."""
    response = api_client_as(Role.SUPERVISOR).get(f"{API}/reports/kpis/")
    assert response.status_code == 200
    assert "stock_value" in response.data


def test_schema_lists_all_endpoints(admin_client) -> None:
    """El esquema OpenAPI incluye todos los recursos del plan."""
    schema = admin_client.get("/api/schema/?format=json").json()
    paths = " ".join(schema["paths"])
    for resource in (
        "categories", "brands", "uoms", "products", "warehouses", "locations",
        "suppliers", "customers", "lots", "stock", "movements/receive",
        "movements/issue", "movements/transfer", "movements/adjust",
        "purchase-orders/{id}/receive", "sales-orders/{id}/suggest-picking",
        "sales-orders/{id}/ship", "cycle-counts/{id}/approve", "lint-runs/run",
        "reports/kpis", "auth/token",
    ):
        assert resource in paths, resource
