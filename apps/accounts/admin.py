"""Admin de Django para ``accounts``."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class UserAdminConfig(UserAdmin):
    """Admin que extiende ``UserAdmin`` con campos extra."""

    list_display = ("username", "email", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff", "is_superuser", "groups")
    search_fields = ("username", "first_name", "last_name", "email")
    fieldsets = UserAdmin.fieldsets + (
        ("StockFlow", {"fields": ("phone", "default_warehouse", "role")}),
    )
