"""Pruebas del inicio y navegación del ERP."""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_user_home_has_accessible_spanish_navigation(client, usuario_ficticio):
    client.force_login(usuario_ficticio)

    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert b"Inicio" in response.content
    assert ("Administraci" + "\u00f3n").encode() not in response.content
    assert (
        'aria-label="Navegaci' + "\u00f3" + 'n principal"'
    ).encode() in response.content


def test_administrator_sees_admin_link(client, administrador_ficticio):
    client.force_login(administrador_ficticio)

    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert b'href="/admin/"' in response.content
    assert ("Administraci" + "\u00f3n").encode() in response.content


def test_user_cannot_access_django_admin(client, usuario_ficticio):
    client.force_login(usuario_ficticio)

    response = client.get(reverse("admin:index"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("admin:login"))
