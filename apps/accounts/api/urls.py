"""URLs de la API REST para ``accounts``: obtencion de token."""

from __future__ import annotations

from django.urls import path
from rest_framework.authtoken.views import ObtainAuthToken

urlpatterns = [
    path("token/", ObtainAuthToken.as_view(), name="token"),
]
