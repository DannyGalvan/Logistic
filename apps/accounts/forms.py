"""Formularios de la app ``accounts``.

Tres formularios:

- ``LoginForm``: extiende ``AuthenticationForm`` para agregar el campo
  ``remember_me`` y textos en espanol.
- ``UserForm``: alta/edicion de usuarios (sin password; se cambia por
  separado con ``PasswordChangeForm``).
- ``ProfileForm``: edicion limitada por el propio usuario.
"""

from __future__ import annotations

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import User
from .roles import Role

ROLE_CHOICES = [("", "— Sin rol —"), *((str(r), str(r)) for r in Role)]


class LoginForm(AuthenticationForm):
    """Formulario de inicio de sesion en espanol."""

    username = forms.CharField(
        label=_("Usuario"),
        widget=forms.TextInput(attrs={"autofocus": True}),
    )
    password = forms.CharField(
        label=_("Contrasena"),
        strip=False,
        widget=forms.PasswordInput,
    )


class UserForm(forms.ModelForm):
    """Formulario de alta/edicion de usuarios (sin password)."""

    role = forms.ChoiceField(choices=ROLE_CHOICES, required=False, label=_("Rol"))

    class Meta:
        """Configuracion del formulario de usuarios."""

        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "default_warehouse",
            "role",
            "is_active",
            "is_staff",
        ]
        labels = {
            "username": _("Usuario"),
            "first_name": _("Nombre"),
            "last_name": _("Apellido"),
            "email": _("Correo"),
            "phone": _("Telefono"),
            "default_warehouse": _("Almacen por defecto"),
            "role": _("Rol"),
            "is_active": _("Activo"),
            "is_staff": _("Acceso al admin"),
        }


class UserCreateForm(UserCreationForm):
    """Formulario de alta de usuarios con password."""

    role = forms.ChoiceField(choices=ROLE_CHOICES, required=False, label=_("Rol"))

    class Meta(UserCreationForm.Meta):
        """Hereda campos y agrega los extras de StockFlow."""

        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "default_warehouse",
            "role",
            "is_active",
            "is_staff",
        ]

    def clean_password2(self) -> str:
        """Valida que las dos contrasenas coincidan."""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                _("Las contrasenas no coinciden."),
                code="password_mismatch",
            )
        password_validation.validate_password(password2, self.instance)
        return password2


class ProfileForm(forms.ModelForm):
    """Formulario de perfil (el usuario edita sus propios datos)."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]
        labels = {
            "first_name": _("Nombre"),
            "last_name": _("Apellido"),
            "email": _("Correo"),
            "phone": _("Telefono"),
        }


__all__ = [
    "LoginForm",
    "UserForm",
    "UserCreateForm",
    "ProfileForm",
]
