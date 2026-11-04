"""F54: ingreso centrado con la marca grande, con datos ficticios."""

import re
from pathlib import Path

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

pytestmark = pytest.mark.django_db

NOMBRE = "Notaría Ficticia de Prueba"
DIRECCION = "Av. Ficticia 123, Distrito de Prueba"


def _ingreso(client):
    contenido = client.get(reverse("login")).content.decode()
    inicio = contenido.index('<p class="ingreso-pie">')
    return contenido, contenido[inicio : contenido.index("</p>", inicio)]


@override_settings(ERP_NOMBRE=NOMBRE, ERP_DIRECCION=DIRECCION, ERP_LOGO="")
def test_tarjeta_unica_con_la_notaria_al_pie(client):
    contenido, pie = _ingreso(client)

    assert "ingreso-banda" not in contenido
    assert contenido.count('<main class="ingreso-main"') == 1
    assert f"<strong>{NOMBRE}</strong>" in pie
    assert DIRECCION in pie


@override_settings(ERP_NOMBRE=NOMBRE, ERP_DIRECCION="")
def test_sin_direccion_no_quedan_huecos(client):
    contenido, pie = _ingreso(client)

    assert "ingreso-direccion" not in contenido
    assert pie == f'<p class="ingreso-pie"><strong>{NOMBRE}</strong>'


@override_settings(ERP_ICONO="/static/marca/icono-ficticio.png")
def test_ingreso_usa_el_icono_configurado(client):
    contenido, _ = _ingreso(client)

    assert '<link rel="icon" href="/static/marca/icono-ficticio.png">' in contenido


@override_settings(ERP_ICONO="")
def test_sin_icono_no_hay_enlace_de_icono(client):
    contenido, _ = _ingreso(client)

    assert 'rel="icon"' not in contenido


@override_settings(ERP_NOMBRE=NOMBRE, ERP_LOGO="/static/marca/logo-ficticio.png")
def test_ingreso_usa_el_logo_configurado(client):
    contenido, _ = _ingreso(client)

    assert (
        f'<img class="marca-logo" src="/static/marca/logo-ficticio.png" alt="{NOMBRE}">'
        in contenido
    )
    assert "marca-sello" not in contenido


@override_settings(ERP_NOMBRE=NOMBRE, ERP_LOGO="")
def test_ingreso_sin_logo_usa_el_sello(client):
    contenido, _ = _ingreso(client)

    assert '<span class="marca-sello" aria-hidden="true">NF</span>' in contenido
    assert "<img" not in contenido


def test_ingreso_no_carga_recursos_remotos(client):
    contenido, _ = _ingreso(client)
    css = (Path(settings.STATICFILES_DIRS[0]) / "css" / "erp.css").read_text(
        encoding="utf-8"
    )

    referencias = re.findall(r'(?:src|href)="([^"]*)"', contenido)
    assert referencias
    assert all(r.startswith(("/", "#")) for r in referencias)
    assert re.search(r'href="/static/css/erp\.css\?v=\w+"', contenido)
    assert "url(" not in contenido
    assert "@import" not in css
    assert all(u.startswith('"data:') for u in re.findall(r"url\(([^)]*)", css))
