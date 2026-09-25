"""Contrato puro de personas con datos enteramente ficticios."""

import pytest

from nucleo.verificar import (
    Catalogo,
    Persona,
    Procedencia,
    _linea_etiquetada,
    catalogo,
    clasificar_pagina,
    comparar_personas,
    revisar,
    unificar_personas,
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
    assert resultado.paginas_no_clasificadas == ()


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


def test_comparar_personas_detecta_documentos_intercambiados():
    fuentes = catalogo(
        {
            "cliente-ficticio.txt": (
                "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000011\f"
                "BRUNO TELURIO NEBULOSA, DE NACIONALIDAD PERUANA. DNI 90000022"
            )
        }
    )
    observaciones = comparar_personas(
        fuentes,
        "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000022\n"
        "BRUNO TELURIO NEBULOSA, DE NACIONALIDAD PERUANA. DNI 90000011",
    )

    assert [observacion["tipo"] for observacion in observaciones] == [
        "DOCUMENTO_CRUZADO",
        "DOCUMENTO_CRUZADO",
    ]
    assert observaciones[0]["nombre"] == "ALBA ZAFIRO LUMARIA"
    assert observaciones[0]["documento_hallado"] == "90000022"
    assert observaciones[0]["documento_esperado"] == "90000011"


def test_comparar_personas_detecta_documento_sin_titular():
    fuentes = catalogo(
        {
            "cliente-ficticio.txt": (
                "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000011"
            )
        }
    )

    observaciones = comparar_personas(
        fuentes,
        "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000099",
    )

    assert len(observaciones) == 1
    assert observaciones[0]["tipo"] == "DOCUMENTO_SIN_TITULAR"
    assert observaciones[0]["documento_hallado"] == "90000099"


def test_unificacion_conservadora_usa_documento_y_nombre_exacto():
    persona_uno = Persona(
        "ALBA ZAFIRO LUMARIA",
        "90000011",
        (Procedencia("biometrica-ficticia.pdf", 1),),
    )
    persona_dos = Persona(
        "LUMARIA, ALBA ZAFIRO",
        "90000011",
        (Procedencia("sunarp-ficticio.pdf", 2),),
    )
    sin_documento_uno = Persona(
        "BRUNO TELURIO NEBULOSA",
        None,
        (Procedencia("declaracion-ficticia.pdf", 1),),
        "SIN_DOCUMENTO",
    )
    sin_documento_dos = Persona(
        "BRUNO TELURIO NEBULOSA",
        None,
        (Procedencia("cliente-ficticio.pdf", 3),),
        "SIN_DOCUMENTO",
    )

    resultado = unificar_personas(
        (persona_uno, persona_dos, sin_documento_uno, sin_documento_dos)
    )

    assert len(resultado) == 2
    assert resultado[0].documento == "90000011"
    assert resultado[0].procedencias == (
        Procedencia("biometrica-ficticia.pdf", 1),
        Procedencia("sunarp-ficticio.pdf", 2),
    )
    assert len(resultado[1].procedencias) == 2


def test_unificacion_no_mezcla_nombres_parecidos_con_documentos_distintos():
    personas = (
        Persona(
            "ALBA ZAFIRO LUMARIA",
            "90000011",
            (Procedencia("cliente-a-ficticio.pdf", 1),),
        ),
        Persona(
            "ALBA ZAFIRO LUMARIA",
            "90000022",
            (Procedencia("cliente-b-ficticio.pdf", 1),),
        ),
    )

    assert unificar_personas(personas) == personas


def test_catalogo_unifica_apellidos_nombres_explicitos_con_mismo_documento():
    resultado = catalogo(
        {
            "prosa-ficticia.txt": (
                "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000011"
            ),
            "sunarp-ficticio.txt": (
                "ZAFIRO LUMARIA, ALBA DE NACIONALIDAD PERUANA. DNI 90000011"
            ),
        }
    )

    assert len(resultado.personas) == 1
    assert resultado.personas[0].nombre == "ALBA ZAFIRO LUMARIA"
    assert len(resultado.personas[0].procedencias) == 2


def test_etiqueta_dni_corrompida_por_ocr_se_acepta_solo_en_forma_cerrada():
    resultado = catalogo(
        {
            "biometrica-ficticia.txt": (
                "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. D.N.1, 90000011"
            )
        }
    )

    assert resultado["DNI"] == {"90000011"}


@pytest.mark.parametrize(
    "linea",
    [
        "DNI 90000011",
        "DNI. 90000011",
        "D.N.I. 90000011",
        "D.N.I. N° 90000011",
        "D.N.1, 90000011",
    ],
)
def test_etiquetas_documentales_cerradas(linea):
    resultado = catalogo(
        {
            "identidad-ficticia.txt": (
                "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. " + linea
            )
        }
    )

    assert resultado["DNI"] == {"90000011"}


@pytest.mark.parametrize(
    "linea",
    [
        "OPERADOR DNI 90000011",
        "USUARIO DNI 90000011",
        "TRANSACCION DNI 90000011",
        "VERIFICACION DNI 90000011",
        "RUC 90000011",
        "TELEFONO 90000011",
        "CORREO DNI 90000011",
    ],
)
def test_numeros_de_metadatos_no_entran_como_documentos(linea):
    resultado = catalogo({"metadatos-ficticios.txt": linea})

    assert resultado["DNI"] == set()


def test_cui_se_extrae_con_su_control_y_no_se_unen_grupos_manuscritos():
    resultado = catalogo(
        {
            "reniec-ficticio.pdf": (
                "CUI: 90000011 - 5\nAPELLIDO PATERNO  LUMARIA\n"
                "APELLIDO MATERNO  ZAFIRO\nNOMBRES  ALBA"
            ),
            "manuscrito-ficticio.txt": (
                "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. DNI 9000 00 22"
            ),
        }
    )

    assert "90000011" in resultado["DNI"]
    assert "90000022" not in resultado["DNI"]


def test_nombre_incompatible_con_mismo_documento_no_se_unifica():
    personas = (
        Persona(
            "ALBA ZAFIRO LUMARIA",
            "90000011",
            (Procedencia("cliente-a-ficticio.pdf", 1),),
        ),
        Persona(
            "BRUNO TELURIO NEBULOSA",
            "90000011",
            (Procedencia("cliente-b-ficticio.pdf", 1),),
        ),
    )

    resultado = unificar_personas(personas)

    assert len(resultado) == 2
    assert {persona.estado for persona in resultado} == {"REVISION_MANUAL"}


def test_persona_con_nombre_sin_documento_se_conserva_sin_observacion_documental():
    resultado = catalogo(
        {
            "declaracion-ficticia.txt": (
                "DECLARACION JURADA\n"
                "APELLIDOS: LUMARIA ZAFIRO\n"
                "NOMBRES: ALBA\n"
                "NOMBRES Y APELLIDOS DEL CONYUGE: BRUNO TELURIO NEBULOSA"
            )
        }
    )

    assert (
        Persona(
            "BRUNO TELURIO NEBULOSA",
            None,
            (Procedencia("declaracion-ficticia.txt", 1),),
            "SIN_DOCUMENTO",
        )
        in resultado.personas
    )


@pytest.mark.parametrize(
    ("fuente", "texto", "esperado"),
    [
        (
            "reniec-ficticio.pdf",
            "CUI: 90000031 - 5\n"
            "APELLIDO PATERNO  LUMARIA  APELLIDO MATERNO  ZAFIRO\n"
            "NOMBRES  ALBA  ESTADO CIVIL  SOLTERA",
            "ALBA LUMARIA ZAFIRO",
        ),
        (
            "biometrica-ficticia.txt",
            "INFORMACION PERSONAL\n"
            "PRIMER APELLIDO  LUMARIA  SEGUNDO APELLIDO  ZAFIRO\n"
            "NOMBRES  ALBA\nDNI 90000031",
            "ALBA LUMARIA ZAFIRO",
        ),
        (
            "declaracion-ficticia.txt",
            "DECLARACION JURADA\n"
            "APELLIDOS  LUMARIA ZAFIRO  NOMBRES  ALBA\n"
            "DNI 90000031",
            "ALBA LUMARIA ZAFIRO",
        ),
    ],
)
def test_formularios_en_dos_columnas_conservan_nombre_completo(fuente, texto, esperado):
    assert esperado in catalogo({fuente: texto})["NOMBRE"]


def test_rotulo_no_arrastra_columnas_siguientes_ni_marca_de_agua():
    linea = (
        "PRIMER APELLIDO  LUMARIA  SELLO FICTICIO 20260101 10:20:30  "
        "SEGUNDO APELLIDO  ZAFIRO"
    )

    assert _linea_etiquetada(linea, "PRIMER APELLIDO") == "LUMARIA"
    assert _linea_etiquetada(linea, "SEGUNDO APELLIDO") == "ZAFIRO"


def test_rotulos_numerados_de_declaracion_tambien_respetan_columnas():
    linea = "1. APELLIDOS: LUMARIA ZAFIRO  2. NOMBRES: ALBA"

    assert _linea_etiquetada(linea, "APELLIDOS") == "LUMARIA ZAFIRO"
    assert _linea_etiquetada(linea, "NOMBRES") == "ALBA"


def test_nombre_completo_con_mismo_documento_se_unifica_entre_formularios():
    resultado = catalogo(
        {
            "reniec-ficticio.pdf": (
                "CUI: 90000031 - 5\n"
                "APELLIDO PATERNO  LUMARIA  APELLIDO MATERNO  ZAFIRO\n"
                "NOMBRES  ALBA"
            ),
            "biometrica-ficticia.txt": (
                "INFORMACION PERSONAL\n"
                "PRIMER APELLIDO  LUMARIA  SEGUNDO APELLIDO  ZAFIRO\n"
                "NOMBRES  ALBA\nDNI 90000031"
            ),
        }
    )

    assert resultado.personas == (
        Persona(
            "ALBA LUMARIA ZAFIRO",
            "90000031",
            (
                Procedencia("reniec-ficticio.pdf", 1),
                Procedencia("biometrica-ficticia.txt", 1),
            ),
        ),
    )


def test_pagina_desconocida_sin_identidad_no_se_lista_para_revision():
    resultado = catalogo({"anexo-ficticio.txt": "SELLO FICTICIO SIN DATOS"})

    assert resultado.paginas_no_clasificadas == ()
