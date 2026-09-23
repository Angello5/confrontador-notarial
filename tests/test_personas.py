"""Contrato puro de personas con datos enteramente ficticios."""

import pytest

from nucleo.verificar import (
    Catalogo,
    Persona,
    Procedencia,
    catalogo,
    clasificar_pagina,
    revisar,
)


def test_catalogo_liga_persona_documento_y_procedencia_por_pagina():
    resultado = catalogo(
        {
            "legajo-ficticio.txt": (
                "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000011"
                "\f"
                "BRUNO TELURIO NEBULOSA, DE NACIONALIDAD PERUANA. DNI 90000022"
            )
        }
    )

    assert isinstance(resultado, Catalogo)
    assert resultado.personas == (
        Persona(
            "ALBA ZAFIRO LUMARIA",
            "90000011",
            (Procedencia("legajo-ficticio.txt", 1),),
        ),
        Persona(
            "BRUNO TELURIO NEBULOSA",
            "90000022",
            (Procedencia("legajo-ficticio.txt", 2),),
        ),
    )


def test_catalogo_proyecta_vista_historica_sin_estado_mutable():
    resultado = catalogo(
        {
            "fuente-ficticia.txt": (
                "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA."
                " DNI 90000011 PARTIDA N° 80000001 S/ 10.00"
            )
        }
    )

    assert resultado["NOMBRE"] == {"ALBA ZAFIRO LUMARIA"}
    assert resultado.get("DNI") == {"90000011"}
    assert resultado["PARTIDA"] == {"80000001"}
    assert resultado["MONTO"] == {"10.00"}
    with pytest.raises(AttributeError):
        resultado["DNI"].add("90000022")


def test_revisar_conserva_salida_legacy_con_la_proyeccion_nueva():
    fuentes = {
        "fuente-ficticia.txt": (
            "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000011"
        )
    }
    destino = "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000012"

    legacy = {
        "NOMBRE": {"ALBA ZAFIRO LUMARIA"},
        "DNI": {"90000011"},
        "PARTIDA": set(),
        "MONTO": set(),
    }
    assert revisar(catalogo(fuentes), destino, 88) == revisar(legacy, destino, 88)


@pytest.mark.parametrize(
    ("texto", "tipo"),
    [
        ("", "BLANCA_SEPARADOR"),
        ("CONSULTA REALIZADA\nCOINCIDENCIAS: 0", "SISGEN"),
        (
            "CUI: 90000011 - 5\nAPELLIDO PATERNO  LUMARIA\n"
            "APELLIDO MATERNO  ZAFIRO\nNOMBRES  ALBA",
            "RENIEC",
        ),
        (
            "INFORMACION PERSONAL\nPrimer Apellido  LUMARIA\n"
            "Segundo Apellido  ZAFIRO\nNombres  ALBA",
            "BIOMETRICA",
        ),
        (
            "DECLARACION JURADA\nApellidos: LUMARIA ZAFIRO\n"
            "Nombres: ALBA\nDNI: 90000011",
            "DECLARACION_JURADA",
        ),
        ("PARTIDA ELECTRONICA N° 80000001\nASIENTO B00001", "SUNARP"),
        ("DNI 90000011\nFICHA DE IDENTIDAD", "IDENTIDAD"),
        ("ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA.", "PROSA"),
        ("SELLO FICTICIO SIN DATOS", "DESCONOCIDA"),
    ],
)
def test_clasificacion_de_pagina_es_determinista_y_conservadora(texto, tipo):
    assert clasificar_pagina(texto) == tipo


def test_catalogo_descarta_solo_separadores_y_sisgen_y_conserva_campos_no_identitarios():
    resultado = catalogo(
        {
            "fuente-ficticia.txt": (
                "SELLO FICTICIO SIN DATOS"
                "\f"
                "\f"
                "CONSULTA REALIZADA\nCOINCIDENCIAS: 0\n"
                "DOCUMENTO IDENTIFICATIVO: DNI 90000022\n"
                "PARTIDA N° 80000002\n"
                "\f"
                "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000011\n"
                "PARTIDA N° 80000003 S/ 20.00"
            )
        }
    )

    assert resultado["DNI"] == {"90000011"}
    assert resultado["PARTIDA"] == {"80000002", "80000003"}
    assert resultado["MONTO"] == {"20.00"}
    assert [(p.pagina, p.tipo) for p in resultado.paginas_descartadas] == [
        (2, "BLANCA_SEPARADOR"),
        (3, "SISGEN"),
    ]
    assert [(p.pagina, p.tipo) for p in resultado.paginas_no_clasificadas] == [
        (1, "DESCONOCIDA")
    ]


def test_catalogo_no_descarta_paginas_identitarias_por_confusion_de_tipo():
    resultado = catalogo(
        {
            "fuente-ficticia.txt": (
                "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000011"
                "\f"
                "DECLARACION JURADA\nApellidos: LUMARIA ZAFIRO\n"
                "Nombres: ALBA\nDNI: 90000011"
            )
        }
    )

    assert resultado.paginas_descartadas == ()
    assert len(resultado.personas) >= 1
