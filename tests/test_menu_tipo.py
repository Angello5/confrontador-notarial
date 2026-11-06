"""El submenú marca Kardex o Transferencia vehicular según el expediente, en todas sus páginas."""

import re
from datetime import datetime

import pytest
from django.urls import reverse

from tests.test_inicio import LIMA, _corrida, _expediente

pytestmark = pytest.mark.django_db

KARDEX, TV = reverse("expediente_lista"), reverse("vehicular_lista")


def _marcados(contenido):
    submenu = contenido[contenido.index('<ul class="submenu"') :]
    submenu = submenu[: submenu.index("</ul>")]
    return re.findall(r'<a href="([^"]+)" aria-current="page"', submenu)


def _paginas(expediente, corrida):
    pk = expediente.pk
    return {
        "detalle": reverse("expediente_detalle", args=[pk]),
        "editar": reverse("expediente_editar", args=[pk]),
        "eliminar": reverse("expediente_eliminar", args=[pk]),
        "historial": reverse("expediente_historial", args=[pk]),
        "corrida": reverse("corrida_detalle", args=[pk, corrida.pk]),
    }


@pytest.mark.parametrize(
    ("tipo", "esperado"), [("NOTARIAL", KARDEX), ("VEHICULAR", TV)]
)
def test_submenu_respeta_el_tipo_en_cada_pagina(
    client, administrador_ficticio, tipo, esperado
):
    expediente = _expediente(f"FICTICIO-MENU-{tipo}", administrador_ficticio, tipo)
    corrida = _corrida(
        expediente, administrador_ficticio, datetime(2026, 10, 12, 10, 0, tzinfo=LIMA)
    )
    client.force_login(administrador_ficticio)

    paginas = {"lista": esperado, **_paginas(expediente, corrida)}
    for nombre, url in paginas.items():
        respuesta = client.get(url)
        assert respuesta.status_code == 200, nombre
        contenido = respuesta.content.decode()
        assert _marcados(contenido) == [esperado], nombre
        # Misma jerarquía en kardex y TV: Expedientes › tipo › …
        migas = contenido[contenido.index('class="migas"') :]
        assert re.match(r'class="migas">\s*<ol>\s*<li>Expedientes</li>', migas), nombre


@pytest.mark.parametrize(
    ("tipo", "primer_paso"), [("NOTARIAL", "Recaudos"), ("VEHICULAR", "Información")]
)
def test_riel_nombra_el_primer_paso_como_su_zona(
    client, administrador_ficticio, tipo, primer_paso
):
    expediente = _expediente(f"FICTICIO-RIEL-{tipo}", administrador_ficticio, tipo)
    client.force_login(administrador_ficticio)

    contenido = client.get(reverse("expediente_detalle", args=[expediente.pk]))
    assert f"<li>{primer_paso}</li><li>Borrador</li>" in contenido.content.decode()


def test_inicio_no_marca_ningun_tipo(client, administrador_ficticio):
    client.force_login(administrador_ficticio)

    assert _marcados(client.get(reverse("home")).content.decode()) == []
