"""F23: reglas deterministas de gramática y redacción, con datos ficticios."""

import pytest

from nucleo.correccion import coincidencias
from nucleo.ortografia import redaccion, revisar


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("EL PRECIO DE DE LA COMPRA", [("DE DE", "palabra repetida", "DE")]),
        ("ALBA , VENDEDORA", [("ALBA ,", "espacio antes de signo", "ALBA,")]),
        ("CONSTE .", [("CONSTE .", "espacio antes de signo", "CONSTE.")]),
        (
            "LA VENTA (SEGUN MINUTA ES LIBRE",
            [("LA VENTA (SEGUN MINUTA ES LIBRE", "falta cerrar el paréntesis", "?")],
        ),
        (
            'DENOMINADO "LOTE UNO',
            [('DENOMINADO "LOTE UNO', "falta cerrar la comilla", "?")],
        ),
        (
            "DENOMINADO «LOTE UNO",
            [("DENOMINADO «LOTE UNO", "falta cerrar la comilla", "?")],
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
        # F58: comillas rectas anidadas dentro de las tipográficas
        '“EL PREDIO "LOTE UNO" ES FICTICIO” Y «VER ("ANEXO")»',
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


_RELLENO = "LAS PARTES FICTICIAS DECLARAN CONOCER EL CONTRATO. " * 6


def test_comilla_tipografica_cerrada_con_recta_en_una_linea_larga():
    """F58: fragmento corto y ubicable, motivo concreto y cierre correcto."""
    texto = (
        f'{_RELLENO}DE LA EMPRESA DENOMINADA “INVERSIONES FICTICIAS E.I.R.L.", '
        f"QUE SE CONSTITUYE {_RELLENO}"
    )
    esperado = [
        (
            '“INVERSIONES FICTICIAS E.I.R.L."',
            'comilla “ cerrada con comilla recta "',
            "“INVERSIONES FICTICIAS E.I.R.L.”",
        )
    ]
    assert len(texto) > 600
    assert redaccion(texto, ()) == esperado
    # un dato protegido entre las comillas no oculta la observación
    assert redaccion(texto, {"INVERSIONES FICTICIAS E.I.R.L."}) == esperado
    assert coincidencias(texto, esperado[0][0])


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        (
            'DENOMINADO "LOTE UNO” Y',
            ('"LOTE UNO”', 'comilla recta " cerrada con comilla ”', '"LOTE UNO"'),
        ),
        # con el cierre correcto más adelante, la comilla recta puede ser otra cosa
        (
            'TUBO “DE 3" PULGADAS”',
            ('“DE 3"', 'comilla “ cerrada con comilla recta "', "?"),
        ),
    ],
)
def test_comilla_cerrada_con_otro_signo(texto, esperado):
    assert redaccion(texto, ()) == [esperado]


def test_signo_sin_cerrar_en_linea_larga_da_una_ventana_corta():
    texto = "PRIMERA PALABRA " * 10 + "(VER LA CLAUSULA SEXTA " + "OTRA PALABRA " * 10
    ((fragmento, motivo, sugerencia),) = redaccion(texto, ())
    assert "(VER LA CLAUSULA SEXTA" in fragmento
    assert len(fragmento) <= 80
    assert coincidencias(texto, fragmento)
    assert (motivo, sugerencia) == ("falta cerrar el paréntesis", "?")


def test_parentesis_se_evalua_por_linea_y_en_orden():
    texto = "LA VENTA (UNO)\nEL PRECIO (DOS\nLA CONTRATO"
    assert redaccion(texto, ()) == [
        ("EL PRECIO (DOS", "falta cerrar el paréntesis", "?"),
        ("LA CONTRATO", "concordancia de artículo", "EL CONTRATO"),
    ]


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        # F39: la letra cambiada se marca en minúscula dentro de la palabra
        (
            "LA PARTE Y lA OTORGANTE",
            [("lA", "mayúsculas y minúsculas mezcladas", "LA")],
        ),
        (
            "EMPRESA DE CREDITOz",
            [("CREDITOz", "mayúsculas y minúsculas mezcladas", "?")],
        ),
        ("PAGA A EL EL/LOS ACREEDOR/ES", [("EL EL", "palabra repetida", "EL")]),
    ],
)
def test_errores_de_tipeo(texto, esperado):
    assert redaccion(texto, ()) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "AVISOS POR WhatsApp AL 900000001",
        "INSCRITO EN EL ASIENTO NºD00002 Y EN EL Nº 5",
        "Mz. A Lt. 5, Jr. Sol, Av. Luna, AVENIDA Avenida avenida",
        # departamento, provincia y distrito homónimos; apellidos iguales
        "DISTRITO DE LUNARIA, PROVINCIA LUNARIA LUNARIA",
        "ALBA ZAFIRO ZAFIRO",
    ],
)
def test_formas_validas_no_son_tipeo(texto):
    assert redaccion(texto, ()) == []


class _Diccionario:
    """Castellano mínimo de los textos ficticios."""

    COMUNES = {
        "autoriza",
        "abogada",
        "con",
        "empresa",
        "de",
        "inscrito",
        "en",
        "el",
        "asiento",
        "reg",
    }

    def lookup(self, palabra):
        return palabra.lower() in self.COMUNES


def test_ortografia_omite_iniciales_abogado_y_minuscula_intercalada():
    texto = (
        "AUTORIZA: ZELMA QUIRVANTA OLMEDA, ABOGADA CON REG. Nº 1\n"
        "-/@/ -/@/ XQZ / -/@/\n"
        "EMPRESA DE CREDITOz INSCRITO EN EL ASIENTO NºD00002 ZELMORIND"
    )
    assert revisar(texto, _Diccionario(), ["zelmorinda"], set()) == [
        ("ZELMORIND", "no existe en castellano", "zelmorinda")
    ]


def test_acento_grave_con_correccion_exacta_salvo_si_esta_en_las_fuentes():
    """F39; FR-002b: lo que la minuta ya trae se da por conocido."""
    texto = "CLÀUSULA SÈTIMA, la resoluciòn"
    assert revisar(texto, _Diccionario(), [], set(), extra={"CLÀUSULA"}) == [
        ("SÈTIMA", "acento grave", "SÉTIMA"),
        ("resoluciòn", "acento grave", "resolución"),
    ]
