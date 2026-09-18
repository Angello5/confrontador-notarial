"""Pruebas de acceso con cuentas ficticias."""

import re

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse

pytestmark = pytest.mark.django_db
CLAVE_PRUEBA = "Clave-ficticia-81!"


def test_enabled_user_can_log_in(client):
    get_user_model().objects.create_user(
        username="cuenta_activa", password=CLAVE_PRUEBA
    )

    response = client.post(
        reverse("login"),
        {"username": "cuenta_activa", "password": CLAVE_PRUEBA},
    )

    assert response.status_code == 302
    assert response.url == "/"


def test_invalid_and_inactive_accounts_receive_the_same_error(client):
    inactive = get_user_model().objects.create_user(
        username="cuenta_inactiva", password=CLAVE_PRUEBA, is_active=False
    )

    invalid_response = client.post(
        reverse("login"),
        {"username": "no_existe", "password": CLAVE_PRUEBA},
    )
    inactive_response = client.post(
        reverse("login"),
        {"username": inactive.username, "password": CLAVE_PRUEBA},
    )

    assert invalid_response.status_code == 200
    assert inactive_response.status_code == 200
    for response in (invalid_response, inactive_response):
        assert response.content.lower().count(b"no son correctos") == 1
    assert _visible_error(invalid_response.content) == _visible_error(
        inactive_response.content
    )


def _visible_error(content):
    match = re.search(
        r'<div class="alert alert-block alert-danger">\s*<ul class="m-0">.*?</ul>\s*</div>',
        content.decode(),
        re.DOTALL,
    )
    assert match
    return match.group()


def test_logout_confirms_success(client, usuario_ficticio):
    client.force_login(usuario_ficticio)

    response = client.post(reverse("logout"))
    messages = list(get_messages(response.wsgi_request))

    assert response.status_code == 302
    assert messages[0].level_tag == "info"
    assert str(messages[0]) == "Cerró sesión correctamente."


def test_anonymous_user_is_redirected_from_protected_home(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response.url == f"{reverse('login')}?next=/"
