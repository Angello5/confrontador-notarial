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
    assert b":class=\"{ 'sidebar-open': menuAbierto }\"" in response.content
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
    assert client.get(reverse("admin:index")).status_code == 200


def test_admin_link_and_access_require_both_staff_and_administrator_group(client, db):
    from django.contrib.auth.models import Group

    admin_group = Group.objects.get(name="Administrador")
    admin_without_staff = get_user_model().objects.create_user(
        username="grupo_sin_staff"
    )
    admin_without_staff.groups.add(admin_group)
    client.force_login(admin_without_staff)
    response = client.get(reverse("home"))
    assert b'href="/admin/"' not in response.content
    assert client.get(reverse("admin:index")).status_code in (302, 403)

    staff_without_admin_group = get_user_model().objects.create_user(
        username="staff_sin_grupo", is_staff=True
    )
    staff_without_admin_group.groups.add(Group.objects.get(name="Usuario"))
    client.force_login(staff_without_admin_group)
    response = client.get(reverse("home"))
    assert b'href="/admin/"' not in response.content
    assert client.get(reverse("admin:index")).status_code in (302, 403)


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
    assert re.search(r'<label[^>]*for="id_password"[^>]*>\s*Clave', content)


def test_adminlte_asset_is_available_locally():
    assert finders.find("vendor/adminlte/adminlte.min.css")


def test_alpine_asset_is_available_locally():
    assert finders.find("vendor/alpine/alpine.min.js")


def test_pending_user_does_not_see_brand_or_navigation(client):
    user = get_user_model().objects.create_user(
        username="cambio_pendiente", force_password_change=True
    )
    client.force_login(user)

    response = client.get(reverse("password_change"))
    content = response.content.decode()

    assert "navbar-brand" not in content
    assert 'id="menu-principal"' not in content
    assert "Abrir o cerrar navegación" not in content
    assert 'class="app-footer"' not in content
    assert "Migas de pan" not in content
    assert "clave temporal" in content
