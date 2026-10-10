"""Tests de ``apps.core.middleware.CurrentUserMiddleware``."""

from __future__ import annotations

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from apps.core.middleware import CurrentUserMiddleware, get_current_user


def _build_request(user):
    """Construye una request con ``user`` para el middleware."""
    factory = RequestFactory()
    request = factory.get("/")
    request.user = user
    return request


def test_middleware_sets_current_user_in_context() -> None:
    """Dentro del middleware ``get_current_user`` devuelve el usuario."""
    captured: list[object] = []

    def view(request):
        captured.append(get_current_user())

    request = _build_request("alice")
    middleware = CurrentUserMiddleware(view)
    middleware(request)
    assert captured == ["alice"]


def test_middleware_resets_context_after_request() -> None:
    """Tras la peticion la ``ContextVar`` vuelve a ``None``.
    """
    captured: list[object] = []

    def view(request):
        captured.append(get_current_user())

    middleware = CurrentUserMiddleware(view)
    middleware(_build_request("bob"))
    assert get_current_user() is None


def test_middleware_handles_anonymous_user() -> None:
    """Una peticion anonima no rompe el middleware."""
    captured: list[object] = []

    def view(request):
        captured.append(get_current_user())

    middleware = CurrentUserMiddleware(view)
    middleware(_build_request(AnonymousUser()))
    assert isinstance(captured[0], AnonymousUser)
