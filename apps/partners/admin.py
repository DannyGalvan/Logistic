"""Admin de Django para ``partners``."""

from __future__ import annotations

from django.contrib import admin

from .models import Customer, Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Admin de proveedores."""

    list_display = ("tax_id", "name", "email", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "tax_id", "contact_name")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin de clientes."""

    list_display = ("tax_id", "name", "email", "credit_limit", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "tax_id", "contact_name")
