"""F54: ingreso con la marca más grande y la banda completa, con datos ficticios."""

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
    inicio = contenido.index('<aside class="ingreso-banda"')
    return contenido, contenido[inicio : contenido.index("</aside>", inicio)]


@override_settings(ERP_NOMBRE=NOMBRE, ERP_DIRECCION=DIRECCION, ERP_LOGO="")
def test_banda_muestra_la_notaria_y_lo_que_hace_el_sistema(client):
    _, banda = _ingreso(client)

    assert "aria-hidden" not in banda.split(">", 1)[0]
    assert NOMBRE in banda and DIRECCION in banda
    assert banda.count("<li>") == 3
    for texto in ("la minuta y los recaudos", "debe decir", "Word"):
        assert texto in banda


@override_settings(ERP_NOMBRE=NOMBRE, ERP_DIRECCION="")
def test_sin_direccion_no_quedan_huecos(client):
    contenido, banda = _ingreso(client)

    assert NOMBRE in banda
    assert "ingreso-direccion" not in contenido
    assert f'<p class="ingreso-pie">{NOMBRE}</p>' in contenido


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
    css = (Path(settings.STATICFILES_DIRS[0]) / "css" / "erp.css").read_text()

    referencias = re.findall(r'(?:src|href)="([^"]*)"', contenido)
    assert referencias and all(r.startswith(("/", "#")) for r in referencias)
    assert re.search(r'href="/static/css/erp\.css\?v=\w+"', contenido)
    assert "url(" not in contenido and "@import" not in css
    assert all(u.startswith('"data:') for u in re.findall(r"url\(([^)]*)", css))
