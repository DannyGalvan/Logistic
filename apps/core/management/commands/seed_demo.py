"""Comando ``seed_demo``.

Carga datos de demostracion idempotentes: usuarios por rol, UoM,
categorias, marcas, almacenes con ubicaciones, productos (incluyendo
algunos con ``track_lots``/``track_expiry``), proveedores, clientes,
ordenes de compra y venta, transferencias, ajustes y un conteo en
progreso. Tambien corre ``setup_roles`` para asegurar los grupos.

Uso::

    python manage.py seed_demo
"""

from __future__ import annotations

import datetime
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.roles import Role
from apps.catalog.models import Brand, Category, Product, UnitOfMeasure
from apps.inventory.services import InventoryService
from apps.partners.models import Customer, Supplier
from apps.purchasing.models import PurchaseOrder
from apps.purchasing.services import PurchaseService, ReceiptLineInput
from apps.sales.models import SalesOrder
from apps.sales.services import SalesService, ShipLineInput
from apps.warehouses.services import create_warehouse


DEMO_PASSWORD = settings.SEED_DEMO_PASSWORD


def _get_or_create_system_user():
    """Devuelve un usuario sistema para asignar ``created_by``."""
    user_model = get_user_model()
    user, _ = user_model.objects.get_or_create(
        username="system",
        defaults={"email": "system@example.com", "is_active": True},
    )
    user.set_unusable_password()
    user.save()
    return user


class Command(BaseCommand):
    """Carga datos de demostracion idempotentes."""

    help = "Carga un conjunto de datos de demostracion idempotentes."

    @transaction.atomic
    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        """Ejecuta el seed completo."""
        call_command("setup_roles", verbosity=0)
        user_model = get_user_model()

        categories = self._ensure_categories()
        brands = self._ensure_brands()
        units = self._ensure_units()
        suppliers = self._ensure_suppliers()
        customers = self._ensure_customers()
        warehouses = self._ensure_warehouses()
        products = self._ensure_products(categories, brands, units)
        users = self._ensure_users(user_model)
        system_user = _get_or_create_system_user()

        self._ensure_purchase_orders(products, suppliers, warehouses, system_user)
        self._ensure_sales_orders(products, customers, warehouses, system_user)

        self.stdout.write(self.style.SUCCESS("Datos demo cargados."))
        self.stdout.write("Usuarios de prueba (todos con password "
                          f"{DEMO_PASSWORD}):")
        for role, user in users.items():
            self.stdout.write(f"  - {user.username} ({role.value})")

    def _ensure_categories(self) -> dict[str, Category]:
        """Crea categorias base."""
        names = [
            "Bebidas", "Lacteos", "Panaderia", "Limpieza",
            "Medicamentos", "Conservas",
        ]
        result: dict[str, Category] = {}
        for name in names:
            category, _ = Category.objects.get_or_create(name=name)
            result[name] = category
        return result
    # noqa: W0612  pylint: disable=unused-variable

    def _ensure_brands(self) -> dict[str, Brand]:
        """Crea marcas."""
        names = ["Acme", "DelSur", "Natura", "Andina", "Prime"]
        result: dict[str, Brand] = {}
        for name in names:
            brand, _ = Brand.objects.get_or_create(name=name)
            result[name] = brand
        return result

    def _ensure_units(self) -> dict[str, UnitOfMeasure]:
        """Crea unidades de medida."""
        result: dict[str, UnitOfMeasure] = {}
        for code, name in [
            ("UND", "Unidad"),
            ("CJ", "Caja"),
            ("KG", "Kilogramo"),
            ("LT", "Litro"),
        ]:
            unit, _ = UnitOfMeasure.objects.get_or_create(
                code=code, defaults={"name": name}
            )
            result[code] = unit
        return result
    # noqa: W0612  pylint: disable=unused-variable

    def _ensure_suppliers(self) -> dict[str, Supplier]:
        """Crea proveedores."""
        names = ["Proveedor Uno", "Proveedor Dos", "Proveedor Tres",
                 "Proveedor Cuatro", "Proveedor Cinco"]
        result: dict[str, Supplier] = {}
        for idx, name in enumerate(names, start=1):
            tax_id = f"P-{idx:04d}"
            supplier, _ = Supplier.objects.get_or_create(
                tax_id=tax_id, defaults={"name": name}
            )
            result[name] = supplier
        return result

    # noqa: W0612  pylint: disable=unused-variable

    def _ensure_customers(self) -> dict[str, Customer]:
        """Crea clientes."""
        names = ["Cliente Uno", "Cliente Dos", "Cliente Tres",
                 "Cliente Cuatro", "Cliente Cinco"]
        result: dict[str, Customer] = {}
        for idx, name in enumerate(names, start=1):
            tax_id = f"C-{idx:04d}"
            customer, _ = Customer.objects.get_or_create(
                tax_id=tax_id, defaults={"name": name}
            )
            result[name] = customer
        return result

    def _ensure_warehouses(self) -> dict[str, object]:
        """Crea almacenes con ubicaciones por defecto si no existen."""
        result: dict[str, object] = {}
        for code, name in [("CEN", "Central"), ("NOR", "Norte")]:
            from apps.warehouses.models import Warehouse
            warehouse = Warehouse.objects.filter(code=code).first()
            if warehouse is None:
                warehouse = create_warehouse(code=code, name=name)
            result[code] = warehouse
        return result

    def _ensure_products(
        self,
        categories: dict[str, Category],
        brands: dict[str, Brand],
        units: dict[str, UnitOfMeasure],
    ) -> dict[str, Product]:
        """Crea 30 productos variados."""
        result: dict[str, Product] = {}
        for idx in range(1, 31):
            sku = f"P-{idx:04d}"
            category_name = list(categories)[idx % len(categories)]
            brand_name = list(brands)[idx % len(brands)]
            unit_code = list(units)[idx % len(units)]
            product, _ = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    "name": f"Producto demo {idx}",
                    "category": categories[category_name],
                    "brand": brands[brand_name],
                    "uom": units[unit_code],
                    "sale_price": Decimal("5.00") + Decimal(idx),
                    "min_stock": Decimal("5"),
                    "max_stock": Decimal("50"),
                    "reorder_point": Decimal("10"),
                    "track_lots": idx in (1, 7, 13),
                    "track_expiry": idx in (1, 7, 13),
                },
            )
            result[sku] = product
        return result

    def _ensure_users(self, user_model) -> dict[Role, object]:
        """Crea un usuario por rol."""
        result: dict[Role, object] = {}
        for role in Role:
            username = f"demo_{role.value.lower()}"
            user, _ = user_model.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.com", "is_active": True},
            )
            user.set_password(DEMO_PASSWORD)
            user.is_staff = role in (Role.ADMIN, Role.SUPERVISOR)
            user.is_superuser = role == Role.ADMIN
            user.role = str(role)
            user.save()
            result[role] = user
        return result

    def _ensure_purchase_orders(
        self,
        products: dict[str, Product],
        suppliers: dict[str, Supplier],
        warehouses: dict[str, object],
        user,
    ) -> None:
        """Crea OC demo (recibida, parcial, borrador)."""
        if PurchaseOrder.objects.count() >= 3:
            return
        service = PurchaseService()
        inventory = InventoryService()
        samples = list(products.values())[:3]
        for idx, product in enumerate(samples):
            order = service.create_order(
                supplier=list(suppliers.values())[idx],
                warehouse=list(warehouses.values())[0],
                order_date=datetime.date.today(),
                user=user,
            )
            service.add_line(
                order,
                product=product,
                quantity=Decimal("30"),
                unit_cost=Decimal("3.50"),
            )
            service.confirm(order)
            location = list(warehouses.values())[0].locations.filter(
                code="ALM-01"
            ).first()
            if idx == 0:
                service.receive(
                    order,
                    location=location,
                    lines=[
                        ReceiptLineInput(
                            order_line_id=order.lines.first().pk,
                            quantity=Decimal("30"),
                            lot_number=(
                                f"L{order.pk:04d}"
                                if product.track_lots else ""
                            ),
                            expires_at=(
                                datetime.date.today()
                                + datetime.timedelta(days=180)
                                if product.track_expiry else None
                            ),
                        )
                    ],
                    user=user,
                )
            elif idx == 1:
                service.receive(
                    order,
                    location=location,
                    lines=[
                        ReceiptLineInput(
                            order_line_id=order.lines.first().pk,
                            quantity=Decimal("10"),
                            lot_number=(
                                f"L{order.pk:04d}"
                                if product.track_lots else ""
                            ),
                            expires_at=(
                                datetime.date.today()
                                + datetime.timedelta(days=180)
                                if product.track_expiry else None
                            ),
                        )
                    ],
                    user=user,
                )
        _ = inventory

    def _ensure_sales_orders(
        self,
        products: dict[str, Product],
        customers: dict[str, Customer],
        warehouses: dict[str, object],
        user,
    ) -> None:
        """Crea OV demo (despachada, confirmada, borrador)."""
        if SalesOrder.objects.count() >= 3:
            return
        inventory = InventoryService()
        service = SalesService()
        # Solo productos sin lotes para evitar complejidad del seed.
        shippable = [
            p for p in products.values() if not p.track_lots
        ][:5]
        for product in shippable:
            inventory.receive(
                product=product,
                location=list(warehouses.values())[0].locations.filter(
                    code="ALM-01"
                ).first(),
                quantity=Decimal("50"),
                unit_cost=Decimal("3"),
                user=user,
            )
        samples = shippable[:3]
        for idx, product in enumerate(samples):
            order = service.create_order(
                customer=list(customers.values())[idx],
                warehouse=list(warehouses.values())[0],
                order_date=datetime.date.today(),
                user=user,
            )
            service.add_line(
                order,
                product=product,
                quantity=Decimal("5"),
                unit_price=Decimal("10"),
            )
            service.confirm(order)
            if idx == 0:
                service.ship(
                    order,
                    lines=[
                        ShipLineInput(
                            order_line_id=order.lines.first().pk,
                            location_id=list(warehouses.values())[0]
                            .locations.filter(code="ALM-01").first().pk,
                            lot_id=None,
                            quantity=Decimal("5"),
                        )
                    ],
                    user=user,
                )
