"""Configuración segura de cookies para HTTP local y HTTPS de producción."""

import importlib
import os


def test_cookie_secure_flags_follow_debug(monkeypatch):
    from config import settings

    original_debug = os.environ.get("DJANGO_DEBUG")
    try:
        for debug in ("true", "false"):
            monkeypatch.setenv("DJANGO_DEBUG", debug)
            reloaded = importlib.reload(settings)

            assert reloaded.SESSION_COOKIE_SECURE is (debug == "false")
            assert reloaded.CSRF_COOKIE_SECURE is (debug == "false")
    finally:
        if original_debug is None:
            monkeypatch.delenv("DJANGO_DEBUG", raising=False)
        else:
            monkeypatch.setenv("DJANGO_DEBUG", original_debug)
        importlib.reload(settings)
