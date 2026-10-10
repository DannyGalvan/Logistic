"""Comando ``seed_demo``.

Carga datos de demostracion idempotentes (plan, seccion 11): usuarios por
rol, unidades, categorias, marcas, almacenes con ubicaciones, 30
productos (algunos con lotes/caducidad FEFO), proveedores, clientes y
operaciones hechas **via services**: 3 OC (recibida, parcial, borrador),
3 OV (despachada, confirmada, borrador), 2 transferencias, 1 ajuste y
1 conteo ciclico en progreso. Deja productos bajo minimo y un lote por
vencer para que existan alertas.

Uso::

    python manage.py seed_demo [--with-lint] [--force]

Con ``DEBUG=False`` se niega a correr salvo que se pase ``--force``.
La contrasena de los usuarios demo sale de ``SEED_DEMO_PASSWORD``.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.roles import Role
from apps.accounts.services import assign_role
from apps.catalog.models import Brand, Category, Product, UnitOfMeasure
from apps.inventory.models import CycleCount, Lot, StockMovement
from apps.inventory.services import (
    AlertService,
    CycleCountService,
    InventoryService,
)
from apps.partners.models import Customer, Supplier
from apps.purchasing.models import PurchaseOrder
from apps.purchasing.services import PurchaseService, ReceiptLineInput
from apps.sales.models import SalesOrder
from apps.sales.services import SalesService, ShipLineInput
from apps.warehouses.models import Location, Warehouse
from apps.warehouses.services import create_location, create_warehouse

DEMO_USERS: dict[Role, str] = {
    Role.ADMIN: "admin",
    Role.SUPERVISOR: "supervisor",
    Role.WAREHOUSE: "almacenista",
    Role.PURCHASING: "compras",
    Role.SALES: "ventas",
    Role.VIEWER: "consulta",
}
CATEGORIES = ["Bebidas", "Lacteos", "Panaderia", "Limpieza", "Medicamentos", "Conservas"]
BRANDS = ["Acme", "DelSur", "Natura", "Andina", "Prime"]
UNITS = [("UND", "Unidad"), ("CJ", "Caja"), ("KG", "Kilogramo"), ("LT", "Litro")]
EXTRA_LOCATIONS = [("ALM-02", "Pasillo 2"), ("ALM-03", "Pasillo 3"), ("ALM-04", "Pasillo 4")]
# SKUs con lote + caducidad (rotacion FEFO): medicamentos y lacteos.
LOT_SKUS = {"P-0001", "P-0005", "P-0010", "P-0014"}
DEMO_REFERENCE = "SEED"


class Command(BaseCommand):
    """Carga datos de demostracion idempotentes."""

    help = "Carga un conjunto de datos de demostracion idempotentes."

    def add_arguments(self, parser):  # type: ignore[no-untyped-def]
        """Argumentos CLI."""
        parser.add_argument(
            "--with-lint", action="store_true",
            help="Ejecuta ademas una corrida inicial de Pylint.",
        )
        parser.add_argument(
            "--force", action="store_true",
            help="Permite ejecutar con DEBUG=False.",
        )

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        """Ejecuta el seed completo."""
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "seed_demo crea usuarios con contrasena conocida; con "
                "DEBUG=False usa --force si realmente lo necesitas."
            )
        with transaction.atomic():
            users = self._seed()
        self.stdout.write(self.style.SUCCESS("Datos demo cargados."))
        self.stdout.write("Usuarios demo (contrasena = SEED_DEMO_PASSWORD):")
        for role, user in users.items():
            self.stdout.write(f"  - {user.username} ({role})")
        if options["with_lint"]:
            call_command("run_pylint", fail_under=0, stdout=self.stdout)

    def _seed(self) -> dict[Role, Any]:
        """Crea maestros y operaciones; devuelve los usuarios por rol."""
        call_command("setup_roles", verbosity=0)
        users = self._ensure_users()
        warehouses = self._ensure_warehouses(users[Role.ADMIN])
        products = self._ensure_products()
        suppliers = self._ensure_partners(Supplier, "Proveedor", "P")
        customers = self._ensure_partners(Customer, "Cliente", "C")
        if not StockMovement.objects.filter(reference=DEMO_REFERENCE).exists():
            self._seed_operations(users, warehouses, products, suppliers, customers)
        return users

    # ------------------------------------------------------------------ maestros
    def _ensure_users(self) -> dict[Role, Any]:
        """Crea (o actualiza) un usuario por rol."""
        user_model = get_user_model()
        result: dict[Role, Any] = {}
        for role, username in DEMO_USERS.items():
            user, _ = user_model.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@stockflow.local"},
            )
            user.set_password(settings.SEED_DEMO_PASSWORD)
            user.is_staff = role in (Role.ADMIN, Role.SUPERVISOR)
            user.is_superuser = role == Role.ADMIN
            user.save()
            result[role] = assign_role(user, role)
        return result

    def _ensure_warehouses(self, user) -> dict[str, Warehouse]:
        """Almacenes ``CEN`` y ``NOR`` con ubicaciones por defecto y extra."""
        result: dict[str, Warehouse] = {}
        for code, name in (("CEN", "Central"), ("NOR", "Norte")):
            warehouse = Warehouse.objects.filter(code=code).first()
            if warehouse is None:
                warehouse = create_warehouse(code=code, name=name, user=user)
            result[code] = warehouse
        central = result["CEN"]
        for code, name in EXTRA_LOCATIONS:
            if not central.locations.filter(code=code).exists():
                create_location(
                    warehouse=central, code=code, name=name,
                    location_type=Location.LocationType.STORAGE,
                )
        return result

    def _ensure_products(self) -> dict[str, Product]:
        """Unidades, categorias, marcas y 30 productos."""
        units = {
            code: UnitOfMeasure.objects.get_or_create(code=code, defaults={"name": name})[0]
            for code, name in UNITS
        }
        categories = [Category.objects.get_or_create(name=n)[0] for n in CATEGORIES]
        brands = [Brand.objects.get_or_create(name=n)[0] for n in BRANDS]
        result: dict[str, Product] = {}
        for idx in range(1, 31):
            sku = f"P-{idx:04d}"
            tracked = sku in LOT_SKUS
            product, _ = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    "name": f"Producto demo {idx}",
                    "category": categories[idx % len(categories)],
                    "brand": brands[idx % len(brands)],
                    "uom": units[UNITS[idx % len(UNITS)][0]],
                    "cost_price": Decimal("3.00") + Decimal(idx) / 10,
                    "sale_price": Decimal("5.00") + Decimal(idx),
                    "min_stock": Decimal("10"),
                    "max_stock": Decimal("100"),
                    "reorder_point": Decimal("15"),
                    "track_lots": tracked,
                    "track_expiry": tracked,
                    "rotation_strategy": "FEFO" if tracked else "FIFO",
                },
            )
            result[sku] = product
        return result

    @staticmethod
    def _ensure_partners(model, label: str, prefix: str) -> list[Any]:
        """Cinco proveedores o clientes."""
        names = ["Uno", "Dos", "Tres", "Cuatro", "Cinco"]
        return [
            model.objects.get_or_create(
                tax_id=f"{prefix}-{idx:04d}",
                defaults={"name": f"{label} {name}"},
            )[0]
            for idx, name in enumerate(names, start=1)
        ]

    # --------------------------------------------------------------- operaciones
    def _seed_operations(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, users, warehouses, products, suppliers, customers,
    ) -> None:
        """Stock inicial, OC, OV, transferencias, ajuste y conteo."""
        keeper = users[Role.WAREHOUSE]
        central = warehouses["CEN"]
        storage = central.locations.get(code="ALM-01")
        self._initial_stock(products, storage, keeper)
        self._purchase_orders(users, central, storage, products, suppliers)
        self._sales_orders(users, central, products, customers)
        self._transfers_and_adjustment(central, warehouses["NOR"], products, keeper)
        cycle_service = CycleCountService()
        if not CycleCount.objects.filter(status="IN_PROGRESS").exists():
            cycle = cycle_service.create(
                warehouse=central, user=keeper,
                location=central.locations.get(code="ALM-02"),
            )
            cycle_service.start(cycle)
        alerts = AlertService()
        for product in products.values():
            alerts.evaluate_product(product)
        alerts.evaluate_expirations()

    @staticmethod
    def _initial_stock(products, storage, user) -> None:
        """Stock base: P-0001..P-0020; P-0018..P-0020 quedan bajo minimo."""
        inventory = InventoryService()
        today = datetime.date.today()
        for idx in range(1, 21):
            product = products[f"P-{idx:04d}"]
            quantity = Decimal("4") if idx >= 18 else Decimal("60")
            lot_kwargs: dict[str, Any] = {}
            if product.track_lots:
                lot_kwargs = {
                    "lot_number": f"L-{idx:04d}-A",
                    # El primer lote del P-0001 vence pronto: genera alerta.
                    "expires_at": today + datetime.timedelta(days=10 if idx == 1 else 240),
                }
            inventory.receive(
                product=product, location=storage, quantity=quantity,
                unit_cost=product.cost_price, user=user,
                reference=DEMO_REFERENCE, reason="OTHER", **lot_kwargs,
            )

    @staticmethod
    def _purchase_orders(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        users, warehouse, storage, products, suppliers,
    ) -> None:
        """OC recibida (con lote), OC parcial y OC en borrador."""
        if PurchaseOrder.objects.exists():
            return
        service = PurchaseService()
        buyer, keeper = users[Role.PURCHASING], users[Role.WAREHOUSE]
        plans = [
            (products["P-0005"], Decimal("30"), Decimal("30")),  # recibida
            (products["P-0021"], Decimal("40"), Decimal("15")),  # parcial
            (products["P-0022"], Decimal("25"), None),           # borrador
        ]
        for idx, (product, quantity, received) in enumerate(plans):
            order = service.create_order(
                supplier=suppliers[idx], warehouse=warehouse,
                order_date=datetime.date.today(), user=buyer,
            )
            line = service.add_line(
                order, product=product, quantity=quantity, unit_cost=product.cost_price,
            )
            if received is None:
                continue
            service.confirm(order)
            service.receive(
                order, location=storage, user=keeper,
                lines=[_receipt_line(order, line, received)],
            )

    @staticmethod
    def _sales_orders(users, warehouse, products, customers) -> None:
        """OV despachada (FEFO sugerido), OV confirmada y OV en borrador."""
        if SalesOrder.objects.exists():
            return
        service = SalesService()
        seller, keeper = users[Role.SALES], users[Role.WAREHOUSE]
        today = datetime.date.today()
        plans = [
            (products["P-0001"], Decimal("6"), "SHIP"),
            (products["P-0002"], Decimal("10"), "CONFIRM"),
            (products["P-0003"], Decimal("3"), "DRAFT"),
        ]
        for idx, (product, quantity, target) in enumerate(plans):
            order = service.create_order(
                customer=customers[idx], warehouse=warehouse,
                order_date=today, user=seller,
            )
            service.add_line(
                order, product=product, quantity=quantity, unit_price=product.sale_price,
            )
            if target == "DRAFT":
                continue
            service.confirm(order)
            if target == "SHIP":
                _ship_suggested(service, order, keeper)

    @staticmethod
    def _transfers_and_adjustment(central, north, products, user) -> None:
        """Dos transferencias (interna y entre almacenes) y un ajuste."""
        inventory = InventoryService()
        storage = central.locations.get(code="ALM-01")
        inventory.transfer(
            product=products["P-0006"], from_location=storage,
            to_location=central.locations.get(code="ALM-02"),
            quantity=Decimal("12"), user=user, reference=DEMO_REFERENCE,
        )
        lot = Lot.objects.filter(product=products["P-0010"]).first()
        inventory.transfer(
            product=products["P-0010"], from_location=storage,
            to_location=north.locations.get(code="ALM-01"),
            quantity=Decimal("20"), user=user, lot=lot, reference=DEMO_REFERENCE,
        )
        inventory.adjust(
            product=products["P-0007"], location=storage,
            counted_quantity=Decimal("57"), user=user,
            note="Merma detectada en revision",
        )


def _receipt_line(order: PurchaseOrder, line, quantity: Decimal) -> ReceiptLineInput:
    """DTO de recepcion con lote y caducidad si el producto los exige."""
    product = line.product
    return ReceiptLineInput(
        order_line_id=line.pk,
        quantity=quantity,
        lot_number=f"L-{order.code}" if product.track_lots else "",
        expires_at=(
            datetime.date.today() + datetime.timedelta(days=365)
            if product.track_expiry else None
        ),
    )


def _ship_suggested(service: SalesService, order: SalesOrder, user) -> None:
    """Despacha la orden completa siguiendo el picking sugerido."""
    service.ship(
        order, user=user, carrier="Transporte propio",
        lines=[
            ShipLineInput(
                order_line_id=row["order_line_id"],
                location_id=row["location_id"],
                lot_id=row["lot_id"],
                quantity=row["quantity"],
            )
            for row in service.suggest_picking(order)
        ],
    )
