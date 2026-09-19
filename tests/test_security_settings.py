"""Configuración segura de cookies para HTTP local y HTTPS de producción."""

import importlib


def test_cookie_secure_flags_follow_debug(monkeypatch):
    from config import settings

    try:
        for debug in ("true", "false"):
            monkeypatch.setenv("DJANGO_DEBUG", debug)
            reloaded = importlib.reload(settings)

            assert reloaded.SESSION_COOKIE_SECURE is (debug == "false")
            assert reloaded.CSRF_COOKIE_SECURE is (debug == "false")
    finally:
        monkeypatch.undo()
        importlib.reload(settings)
