"""Pruebas del inicio y navegación del ERP."""

import re

import pytest
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_user_home_has_accessible_spanish_navigation(client, usuario_ficticio):
    client.force_login(usuario_ficticio)

    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert b"Inicio" in response.content
    assert b"/static/vendor/adminlte/adminlte.min.css" in response.content
    assert b"/static/vendor/alpine/alpine.min.js" in response.content
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


def test_authenticated_account_without_role_cannot_open_erp(client):
    sin_rol = get_user_model().objects.create_user(username="cuenta_sin_rol")
    client.force_login(sin_rol)

    response = client.get(reverse("home"))

    assert response.status_code == 403


def test_login_has_visible_spanish_field_labels(client):
    response = client.get(reverse("login"))

    assert response.status_code == 200
    content = response.content.decode()
    assert re.search(r'<label[^>]*for="id_username"[^>]*>\s*Nombre de usuario', content)
    assert re.search(r'<label[^>]*for="id_password"[^>]*>\s*Contraseña', content)


def test_adminlte_asset_is_available_locally():
    assert finders.find("vendor/adminlte/adminlte.min.css")
