"""Vistas de la app ``accounts``.

- ``LoginView`` reutiliza ``django.contrib.auth.views.LoginView`` con
  la plantilla ``registration/login.html``.
- ``ProfileView`` permite al usuario editar sus datos y cambiar
  contrasena.
- ``UserListView``, ``UserCreateView``, ``UserUpdateView`` y
  ``UserDeactivateView`` implementan el CRUD de usuarios con
  permiso ``accounts.view_user`` y ``accounts.add_user`` etc.
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib.auth.views import LoginView as AuthLoginView
from django.contrib.auth.views import LogoutView as AuthLogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import ProfileForm, UserCreateForm, UserForm
from .models import User


class LoginView(AuthLoginView):
    """Vista de inicio de sesion."""

    template_name = "registration/login.html"
    redirect_authenticated_user = True


class LogoutView(AuthLogoutView):
    """Vista de cierre de sesion."""

    next_page = reverse_lazy("accounts:login")


class ProfileView(LoginRequiredMixin, TemplateView):
    """Vista combinada de perfil + cambio de contrasena."""

    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):  # type: ignore[no-untyped-def]
        """Inyecta formularios en el contexto."""
        context = super().get_context_data(**kwargs)
        context["profile_form"] = ProfileForm(instance=self.request.user)
        context["password_form"] = PasswordChangeForm(self.request.user)
        return context

    def post(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        """Procesa el POST: edicion de perfil o cambio de contrasena."""
        action = request.POST.get("action", "profile")
        if action == "password":
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Contrasena actualizada.")
                return self._redirect_ok(request)
            context = self.get_context_data()
            context["password_form"] = form
            return self.render_to_response(context)
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado.")
            return self._redirect_ok(request)
        context = self.get_context_data()
        context["profile_form"] = form
        return self.render_to_response(context)

    @staticmethod
    def _redirect_ok(request):  # type: ignore[no-untyped-def]
        """Atajo para un redirect con codigo 303 tras POST."""
        _ = request
        return redirect("accounts:profile")


class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de usuarios para administradores."""

    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 20
    permission_required = "accounts.view_user"
    raise_exception = True


class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Alta de usuarios."""

    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user-list")
    permission_required = "accounts.add_user"
    raise_exception = True

    def form_valid(self, form):  # type: ignore[no-untyped-def]
        """Muestra mensaje de exito y guarda el registro."""
        response = super().form_valid(form)
        messages.success(self.request, f"Usuario '{form.instance.username}' creado.")
        return response


class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Edicion de usuarios."""

    model = User
    form_class = UserForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user-list")
    permission_required = "accounts.change_user"
    raise_exception = True

    def form_valid(self, form):  # type: ignore[no-untyped-def]
        """Confirma la operacion con un mensaje legible."""
        response = super().form_valid(form)
        messages.success(self.request, f"Usuario '{form.instance.username}' actualizado.")
        return response


__all__ = [
    "LoginView",
    "LogoutView",
    "ProfileView",
    "UserListView",
    "UserCreateView",
    "UserUpdateView",
]
