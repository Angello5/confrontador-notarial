"""Pruebas del bloqueo persistente de ingreso con cuentas ficticias."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.utils import timezone
from django.urls import reverse

pytestmark = pytest.mark.django_db
CLAVE_PRUEBA = "Clave-ficticia-81!"
CLAVE_INCORRECTA = "Clave-incorrecta-1!"


def test_five_failures_lock_login_and_success_resets_state(client):
    user = get_user_model().objects.create_user(
        username="cuenta_bloqueable", password=CLAVE_PRUEBA
    )

    for _ in range(5):
        assert authenticate(username=user.username, password=CLAVE_INCORRECTA) is None

    user.refresh_from_db()
    assert user.failed_login_attempts == 5
    assert (
        timezone.now()
        < user.login_locked_until
        <= timezone.now() + timedelta(minutes=15)
    )
    assert authenticate(username=user.username, password=CLAVE_PRUEBA) is None

    # Tras el vencimiento, una autenticación correcta elimina el contador y el bloqueo.
    user.login_locked_until = timezone.now() - timedelta(seconds=1)
    user.save(update_fields=["login_locked_until"])
    assert authenticate(username=user.username, password=CLAVE_PRUEBA) == user
    user.refresh_from_db()
    assert user.failed_login_attempts == 0
    assert user.login_locked_until is None


def test_locked_and_nonexistent_users_receive_the_same_generic_error(client):
    user = get_user_model().objects.create_user(
        username="cuenta_bloqueada", password=CLAVE_PRUEBA
    )
    for _ in range(5):
        client.post(
            reverse("login"),
            {"username": user.username, "password": "Clave-incorrecta-1!"},
        )

    blocked = client.post(
        reverse("login"), {"username": user.username, "password": CLAVE_PRUEBA}
    )
    missing = client.post(
        reverse("login"), {"username": "cuenta_inexistente", "password": CLAVE_PRUEBA}
    )

    assert blocked.status_code == missing.status_code == 200
    assert _error_alert(blocked.content) == _error_alert(missing.content)
    assert blocked.content.lower().count(b"no son correctos") == 1


def test_lockout_applies_to_django_admin_login(client):
    user = get_user_model().objects.create_user(
        username="administrador_bloqueable",
        password=CLAVE_PRUEBA,
        is_staff=True,
    )
    for _ in range(5):
        client.post(
            reverse("admin:login"),
            {"username": user.username, "password": "Clave-incorrecta-1!"},
        )

    response = client.post(
        reverse("admin:login"),
        {"username": user.username, "password": CLAVE_PRUEBA},
    )

    assert response.status_code == 200
    assert not response.wsgi_request.user.is_authenticated


@pytest.mark.django_db(transaction=True)
def test_concurrent_failures_do_not_lose_attempts():
    user = get_user_model().objects.create_user(
        username="cuenta_concurrente", password=CLAVE_PRUEBA
    )
    barrera = Barrier(5)

    def intento_fallido(_):
        close_old_connections()
        barrera.wait(timeout=10)
        resultado = authenticate(username=user.username, password=CLAVE_INCORRECTA)
        close_old_connections()
        return resultado

    with ThreadPoolExecutor(max_workers=5) as executor:
        assert list(executor.map(intento_fallido, range(5))) == [None] * 5

    user.refresh_from_db()
    assert user.failed_login_attempts == 5
    assert user.login_locked_until is not None


def _error_alert(content):
    start = content.index(b'<div class="aviso" data-tono="peligro" role="alert">')
    end = content.index(b"</div>", start) + len(b"</div>")
    return content[start:end]
