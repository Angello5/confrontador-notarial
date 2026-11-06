"""F65: lista de observaciones compacta, con datos ficticios."""

import json
import re
from types import SimpleNamespace

import pytest


def _marcado(tramos):
    return "".join(f"[{t}]" if distinto else t for t, distinto in tramos)


@pytest.mark.parametrize(
    ("dice", "debe", "esperado_dice", "esperado_debe"),
    [
        (
            "ALBA LUMARIA ZAFIRA",
            "ALBA LUMARIA ZAFIRO",
            "ALBA LUMARIA [ZAFIRA]",
            "ALBA LUMARIA [ZAFIRO]",
        ),
        (
            "TREINTA Y CINCO POR CIENTO (36%)",
            "TREINTA Y SEIS POR CIENTO (36%)",
            "TREINTA Y [CINCO] POR CIENTO (36%)",
            "TREINTA Y [SEIS] POR CIENTO (36%)",
        ),
        ("90000002", "90000001", "[90000002]", "[90000001]"),
        (
            "CIRO VALDANO",
            "CIRO VALDANO QUINTEL",
            "CIRO VALDANO",
            "CIRO VALDANO [QUINTEL]",
        ),
        ("IGUAL", "IGUAL", "IGUAL", "IGUAL"),
    ],
)
def test_partes_distintas_resalta_solo_lo_que_cambia(
    dice, debe, esperado_dice, esperado_debe
):
    from expedientes.services import partes_distintas

    tramos_dice, tramos_debe = partes_distintas(dice, debe)
    assert (_marcado(tramos_dice), _marcado(tramos_debe)) == (
        esperado_dice,
        esperado_debe,
    )


def test_aviso_con_sugerencia_la_separa_de_la_nota():
    from expedientes.services import aviso_de

    aviso = aviso_de(
        {
            "campo": "NUMERO_EN_LETRAS",
            "hallado": "TREINTA Y CINCO POR CIENTO (36%)",
            "esperado": "36%",
            "detalle": "las letras dicen «35%»; la minuta dice «36%»; se sugiere "
            "corregir las letras «TREINTA Y SEIS POR CIENTO (36%)»",
        }
    )
    assert aviso["nota"] == "La minuta dice 36%."
    assert aviso["rotulo_sugerencia"] == "Se sugiere corregir las letras"
    assert aviso["sugerencia"] == "TREINTA Y SEIS POR CIENTO (36%)"


def test_aviso_sin_sugerencia_no_trae_sugerencia():
    from expedientes.services import aviso_de

    aviso = aviso_de(
        {
            "campo": "AREA",
            "hallado": "CIEN METROS CUADRADOS (120 M2)",
            "esperado": "120 M2",
        }
    )
    assert "sugerencia" not in aviso


def _corrida(regla=(), personas=(), ortografia=()):
    hallazgos = {
        "estado": "RESULTADO",
        "mensaje": "",
        "personas": list(personas),
        "regla": list(regla),
        "ortografia": list(ortografia),
    }
    return SimpleNamespace(hallazgos=json.dumps(hallazgos), presentacion={}, pk=1)


def test_resultado_trae_el_cambio_resaltado_por_fila():
    from expedientes.services import resultado_de_corrida

    resultado = resultado_de_corrida(
        _corrida(
            regla=[
                {
                    "campo": "NOMBRE",
                    "hallado": "ALBA ZAFIRA",
                    "esperado": "ALBA ZAFIRO",
                },
                {
                    "campo": "NUMERO_EN_LETRAS",
                    "hallado": "TREINTA Y SEI (36)",
                    "esperado": "36",
                    "detalle": "letras mal escritas; se sugiere «TREINTA Y SEIS (36)»",
                },
                {"campo": "AREA", "hallado": "CIEN (120 M2)", "esperado": "120 M2"},
                {
                    "campo": "NOMBRE",
                    "hallado": "No aparece en el borrador",
                    "esperado": "CIRO VALDANO",
                },
            ],
            ortografia=[{"palabra": "ortografia", "sugerencia": "ortografía"}],
        )
    )
    nombre, numero, area, falta = resultado["regla"]
    assert falta["cambio"] is None  # «No aparece»: no hay texto que comparar
    assert _marcado(nombre["cambio"]["debe"]) == "ALBA [ZAFIRO]"
    assert _marcado(numero["cambio"]["dice"]) == "TREINTA Y [SEI] (36)"
    assert _marcado(numero["cambio"]["debe"]) == "TREINTA Y [SEIS] (36)"
    assert area["cambio"] is None  # aviso sin sugerencia: nada que resaltar
    assert _marcado(resultado["ortografia"][0]["cambio"]["debe"]) == "[ortografía]"


def test_marca_con_logo_trae_el_sello_de_reemplazo():
    from django.template.loader import render_to_string

    html = render_to_string(
        "core/_marca.html",
        {
            "erp_logo": "/static/logo-ficticio.png",
            "erp_nombre": "Notaría Ficticia",
            "erp_iniciales": "NF",
        },
    )
    assert 'onerror="' in html
    assert re.search(r'class="marca-fila[^"]*"[^>]*hidden', html)
    assert "NF" in html and "Notaría Ficticia" in html


@pytest.mark.django_db
def test_pantalla_sin_panel_de_detalle(client, usuario_ficticio, monkeypatch):
    from expedientes.models import Expediente
    from tests.flujo_confrontacion import confrontar_y_ver
    from tests.test_expedientes_confrontacion_ui import _documentos

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-F65", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    monkeypatch.setattr(
        "expedientes.services.confrontar_borrador",
        lambda expediente, documento, **kwargs: {
            "estado": "RESULTADO",
            "regla": [
                {
                    "formato": "regla",
                    "campo": "NOMBRE",
                    "hallado": "ALBA ZAFIRA",
                    "esperado": "ALBA ZAFIRO",
                    "motivo": "",
                    "porcentaje": "",
                    "ubicacion": {"linea": 1, "fragmento": "ALBA ZAFIRA"},
                }
            ],
            "ortografia": [],
        },
    )
    client.force_login(usuario_ficticio)
    respuesta = confrontar_y_ver(
        client, f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    )
    html = respuesta.content.decode()
    assert "Detalle de la observación" not in html
    assert "obs-detalle" not in html
    assert "Debe decir" in html
    assert "<mark>ZAFIRO</mark>" in html
    # La casilla de corrección vive en la fila, fuera del botón.
    fila = re.search(r'<li data-id="r1".*?</li>', html, re.S).group(0)
    assert re.search(
        r"</button>\s*<div class=\"obs-abierta\".*?corrDe\('r1'\)", fila, re.S
    )
