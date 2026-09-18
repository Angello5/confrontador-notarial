"""Pruebas de acceso con cuentas ficticias."""

import pytest
from django.contrib.auth import get_user_model
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
    assert b"usuario o la clave no son correctos" in invalid_response.content.lower()
    assert (
        invalid_response.context["form"].non_field_errors()
        == inactive_response.context["form"].non_field_errors()
    )


def test_anonymous_user_is_redirected_from_protected_home(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response.url == f"{reverse('login')}?next=/"
