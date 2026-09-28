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


@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_home_rejects_unsafe_http_methods(client, usuario_ficticio, method):
    client.force_login(usuario_ficticio)

    response = getattr(client, method)(reverse("home"))

    assert response.status_code == 405


def test_home_accepts_safe_http_methods(client, usuario_ficticio):
    client.force_login(usuario_ficticio)

    assert client.get(reverse("home")).status_code == 200
    assert client.head(reverse("home")).status_code == 200


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


# F14 · Rediseño de interfaz


def _crear_expediente(codigo, usuario, *estados):
    from expedientes.models import Documento, Expediente

    expediente = Expediente.objects.create(codigo=codigo, creado_por=usuario)
    for indice, estado in enumerate(estados):
        Documento.objects.create(
            expediente=expediente,
            rol=Documento.CLIENTE,
            nombre_original=f"ficticio-{indice}.txt",
            hash_archivo=f"{codigo}{indice}".lower().ljust(64, "0")[:64],
            tamano_bytes=4,
            estado=estado,
            subido_por=usuario,
        )
    return expediente


def test_erp_css_es_local_y_lo_cargan_base_y_login(client, usuario_ficticio):
    assert finders.find("css/erp.css")
    client.force_login(usuario_ficticio)
    assert b"/static/css/erp.css" in client.get(reverse("home")).content
    client.logout()
    assert b"/static/css/erp.css" in client.get(reverse("login")).content


def test_shell_de_usuario_muestra_marca_pie_y_activo(client, usuario_ficticio):
    client.force_login(usuario_ficticio)

    content = client.get(reverse("home")).content.decode()

    assert '<span class="marca-nombre">ERP Notarial</span>' in content
    assert re.search(r'href="/"[^>]*aria-current="page"', content)
    assert not re.search(r'href="/expedientes/"[^>]*aria-current', content)
    assert "usuario_ficticio" in content
    assert "Usuario</" in content
    assert ">US<" in content
    assert ':aria-expanded="menuAbierto"' in content
    assert "Usuarios y permisos" not in content


def test_shell_marca_expedientes_activo_en_lista_y_detalle(client, usuario_ficticio):
    expediente = _crear_expediente("EXP-FICTICIO-ACTIVO", usuario_ficticio)
    client.force_login(usuario_ficticio)

    for ruta in (reverse("expediente_lista"), f"/expedientes/{expediente.pk}/"):
        content = client.get(ruta).content.decode()
        assert re.search(r'href="/expedientes/"[^>]*aria-current="page"', content)
        assert not re.search(r'href="/"[^>]*aria-current', content)


def test_shell_de_administrador_muestra_seccion_administracion(
    client, administrador_ficticio
):
    client.force_login(administrador_ficticio)

    content = client.get(reverse("home")).content.decode()

    assert "Usuarios y permisos" in content
    assert "Administrador</" in content


def test_inicio_calcula_metricas_con_la_visibilidad_de_la_lista(
    client, usuario_ficticio, administrador_ficticio
):
    _crear_expediente("EXP-FICTICIO-M1", usuario_ficticio)
    _crear_expediente("EXP-FICTICIO-M2", usuario_ficticio, "PENDIENTE", "LISTO")
    _crear_expediente("EXP-FICTICIO-M3", usuario_ficticio, "LISTO")
    _crear_expediente("EXP-FICTICIO-M4", usuario_ficticio, "ERROR")
    _crear_expediente("EXP-FICTICIO-AJENO", administrador_ficticio, "LISTO")
    client.force_login(usuario_ficticio)

    respuesta = client.get(reverse("home"))

    assert respuesta.context["metricas"] == {
        "total": 4,
        "procesando": 1,
        "listos": 1,
        "errores": 1,
    }
    content = respuesta.content.decode()
    assert "EXP-FICTICIO-AJENO" not in content
    assert "Listos para confrontar" in content
    assert 'data-estado="ERROR"' in content

    client.force_login(administrador_ficticio)
    assert client.get(reverse("home")).context["metricas"]["total"] == 5


def test_inicio_lista_los_cinco_mas_recientes_sin_datos_sensibles(
    client, usuario_ficticio
):
    for numero in range(7):
        _crear_expediente(f"EXP-FICTICIO-U{numero}", usuario_ficticio, "LISTO")
    client.force_login(usuario_ficticio)

    respuesta = client.get(reverse("home"))

    codigos = [expediente.codigo for expediente, _ in respuesta.context["ultimos"]]
    assert codigos == [f"EXP-FICTICIO-U{numero}" for numero in range(6, 1, -1)]
    content = respuesta.content.decode()
    assert "EXP-FICTICIO-U1<" not in content
    assert "hash" not in content.lower()
    assert "ficticio-0.txt" not in content
    assert "<caption" in content
    assert "Nueva confrontación" in content
    assert "Control administrativo" not in content


def test_inicio_vacio_ofrece_crear_el_primero(client, usuario_ficticio):
    client.force_login(usuario_ficticio)

    content = client.get(reverse("home")).content.decode()

    assert "<table" not in content
    assert 'href="/expedientes/"' in content
    assert "primer expediente" in content


def test_inicio_de_administrador_ofrece_control_administrativo(
    client, administrador_ficticio
):
    client.force_login(administrador_ficticio)

    content = client.get(reverse("home")).content.decode()

    assert "Control administrativo" in content
    assert "Administrar" in content


def test_plantillas_no_mencionan_ia():
    from pathlib import Path

    for plantilla in Path("templates").rglob("*.html"):
        texto = plantilla.read_text(encoding="utf-8")
        assert not re.search(r"\b(IA|AI)\b", texto), plantilla


def test_mobile_overlay_is_a_keyboard_accessible_button(client, usuario_ficticio):
    client.force_login(usuario_ficticio)

    html = client.get(reverse("home")).content.decode()

    assert re.search(
        r'<button type="button" class="sidebar-overlay" aria-label="Cerrar navegación"'
        r' @click="menuAbierto = false"></button>',
        html,
    )
    assert '<div class="sidebar-overlay"' not in html
