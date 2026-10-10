"""URLs de la app ``accounts``."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("perfil/", views.ProfileView.as_view(), name="profile"),
    path("usuarios/", views.UserListView.as_view(), name="user-list"),
    path(
        "usuarios/nuevo/",
        views.UserCreateView.as_view(),
        name="user-create",
    ),
    path(
        "usuarios/<int:pk>/editar/",
        views.UserUpdateView.as_view(),
        name="user-update",
    ),
]
