"""Pruebas de cambio obligatorio de clave temporal."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

pytestmark = pytest.mark.django_db
CLAVE_TEMPORAL = "Clave-temporal-72!"


@pytest.fixture
def cuenta_pendiente():
    user = get_user_model().objects.create_user(
        username="cambio_pendiente", password=CLAVE_TEMPORAL
    )
    user.force_password_change = True
    user.save()
    return user


def test_temporary_password_requires_password_change_on_login(client, cuenta_pendiente):
    response = client.post(
        reverse("login"),
        {"username": cuenta_pendiente.username, "password": CLAVE_TEMPORAL},
    )

    assert response.status_code == 302
    assert response.url == reverse("password_change")


def test_pending_user_cannot_open_other_routes(client, cuenta_pendiente):
    client.force_login(cuenta_pendiente)

    response = client.get("/")

    assert response.status_code == 302
    assert response.url == reverse("password_change")


def test_pending_user_cannot_open_admin(client, cuenta_pendiente):
    client.force_login(cuenta_pendiente)

    response = client.get(reverse("admin:index"))

    assert response.status_code == 302
    assert response.url == reverse("password_change")


def test_password_change_validates_and_clears_pending_flag(client, cuenta_pendiente):
    client.force_login(cuenta_pendiente)
    path = reverse("password_change")
    invalid = client.post(
        path,
        {
            "old_password": CLAVE_TEMPORAL,
            "new_password1": "corta",
            "new_password2": "distinta",
        },
    )

    assert invalid.status_code == 200
    assert invalid.context["form"].errors
    content = invalid.content.decode()
    assert "Clave actual (temporal)" in content
    assert "Clave nueva" in content
    assert "Confirmar clave nueva" in content

    response = client.post(
        path,
        {
            "old_password": CLAVE_TEMPORAL,
            "new_password1": "Nueva-clave-ficticia-92!",
            "new_password2": "Nueva-clave-ficticia-92!",
        },
    )

    assert response.status_code == 302
    cuenta_pendiente.refresh_from_db()
    assert not cuenta_pendiente.force_password_change
    assert cuenta_pendiente.check_password("Nueva-clave-ficticia-92!")
