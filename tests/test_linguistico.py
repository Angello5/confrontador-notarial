"""F23: reglas deterministas de gramática y redacción, con datos ficticios."""

import pytest

from nucleo.ortografia import redaccion


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("EL PRECIO DE DE LA COMPRA", [("DE DE", "palabra repetida", "DE")]),
        ("ALBA , VENDEDORA", [("ALBA ,", "espacio antes de signo", "ALBA,")]),
        ("CONSTE .", [("CONSTE .", "espacio antes de signo", "CONSTE.")]),
        (
            "LA VENTA (SEGUN MINUTA ES LIBRE",
            [("LA VENTA (SEGUN MINUTA ES LIBRE", "paréntesis sin cerrar", "?")],
        ),
        (
            'DENOMINADO "LOTE UNO',
            [('DENOMINADO "LOTE UNO', "comillas sin cerrar", "?")],
        ),
        (
            "DENOMINADO «LOTE UNO",
            [("DENOMINADO «LOTE UNO", "comillas sin cerrar", "?")],
        ),
        ("LA CONTRATO", [("LA CONTRATO", "concordancia de artículo", "EL CONTRATO")]),
        (
            "DEL CLÁUSULA",
            [("DEL CLÁUSULA", "concordancia de artículo", "DE LA CLÁUSULA")],
        ),
        ("EL PARTIDA", [("EL PARTIDA", "concordancia de artículo", "LA PARTIDA")]),
        (
            "AL ESCRITURA",
            [("AL ESCRITURA", "concordancia de artículo", "A LA ESCRITURA")],
        ),
    ],
)
def test_cada_regla_reporta_su_caso(texto, esperado):
    assert redaccion(texto, ()) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "EL PRECIO DE LA COMPRA ES DE CIEN SOLES.",
        "LA PARTE VENDEDORA, EL CONTRATO Y LA CLÁUSULA PRIMERA; DEL INMUEBLE.",
        'EL PARTE NOTARIAL (DOS COPIAS) Y «LOTE UNO» Y “LOTE DOS” Y "LOTE TRES".',
        "CONSTE ............ FIRMA",
        "DNI 90000001  90000002",
        "LA\tVENTA",
        "LA  PARTE VENDEDORA",
    ],
)
def test_texto_correcto_no_reporta(texto):
    assert redaccion(texto, ()) == []


def test_hallazgo_sobre_dato_protegido_se_descarta():
    texto = "COMPARECE ALBA  LUMARIA ZAFIRO , CON DOMICILIO EN AV. LUNA LUNA 12"
    assert redaccion(texto, {"ALBA LUMARIA ZAFIRO", "AV. LUNA LUNA 12"}) == []


def test_parentesis_se_evalua_por_linea_y_en_orden():
    texto = "LA VENTA (UNO)\nEL PRECIO (DOS\nLA CONTRATO"
    assert redaccion(texto, ()) == [
        ("EL PRECIO (DOS", "paréntesis sin cerrar", "?"),
        ("LA CONTRATO", "concordancia de artículo", "EL CONTRATO"),
    ]
