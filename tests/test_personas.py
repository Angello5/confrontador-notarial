"""Contrato puro de personas con datos enteramente ficticios."""

from datetime import date

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
    revisar_persona_ampliada,
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
    assert resultado.personas == ()
    assert resultado.menciones == (
        Persona(
            "ALBA ZAFIRO LUMARIA",
            "90000011",
            (Procedencia("legajo-ficticio.txt", 1),),
            "SIN_FICHA",
        ),
        Persona(
            "BRUNO TELURIO NEBULOSA",
            "90000022",
            (Procedencia("legajo-ficticio.txt", 2),),
            "SIN_FICHA",
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
    assert len(resultado.menciones) >= 1


_INTERCAMBIADOS = (
    "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000022\n"
    "BRUNO TELURIO NEBULOSA, DE NACIONALIDAD PERUANA. DNI 90000011"
)


def test_comparar_personas_detecta_documentos_intercambiados():
    fuentes = catalogo(
        {
            "fichas-ficticias.txt": (
                "INFORMACION PERSONAL\n"
                "PRIMER APELLIDO  ZAFIRO  SEGUNDO APELLIDO  LUMARIA\n"
                "NOMBRES  ALBA\nDNI 90000011\f"
                "INFORMACION PERSONAL\n"
                "PRIMER APELLIDO  TELURIO  SEGUNDO APELLIDO  NEBULOSA\n"
                "NOMBRES  BRUNO\nDNI 90000022"
            )
        }
    )
    observaciones = comparar_personas(fuentes, _INTERCAMBIADOS)

    assert [observacion["tipo"] for observacion in observaciones] == [
        "DOCUMENTO_CRUZADO",
        "DOCUMENTO_CRUZADO",
    ]
    assert observaciones[0]["nombre"] == "ALBA ZAFIRO LUMARIA"
    assert observaciones[0]["documento_hallado"] == "90000022"
    assert observaciones[0]["documento_esperado"] == "90000011"
    assert observaciones[0]["procedencias"] == (Procedencia("fichas-ficticias.txt", 1),)


def test_comparecientes_sin_ficha_intercambiados_no_dan_documento_cruzado():
    # Consecuencia aceptada de F13: el documento cruzado exige titular con ficha.
    fuentes = catalogo(
        {
            "cliente-ficticio.txt": (
                "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000011\f"
                "BRUNO TELURIO NEBULOSA, DE NACIONALIDAD PERUANA. DNI 90000022"
            )
        }
    )

    assert comparar_personas(fuentes, _INTERCAMBIADOS) == ()


def test_documento_de_la_minuta_sin_ficha_tiene_titular():
    fuentes = catalogo(
        {
            "reniec-ficticio.pdf": _reniec("90000011", "ALBA", "LUMARIA", "ZAFIRO"),
            "minuta-ficticia.txt": (
                "CLARA FICTELIA SOLARIA, DE NACIONALIDAD PERUANA. DNI 90000033"
            ),
        }
    )

    assert (
        comparar_personas(
            fuentes, "CLARA FICTELIA SOLARIA, DE NACIONALIDAD PERUANA. DNI 90000033"
        )
        == ()
    )


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

    assert len(resultado.menciones) == 1
    assert resultado.menciones[0].nombre == "ALBA ZAFIRO LUMARIA"
    assert len(resultado.menciones[0].procedencias) == 2


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


def test_declarante_sin_ficha_es_mencion_con_su_conyuge():
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

    origen = Procedencia("declaracion-ficticia.txt", 1)
    assert resultado.personas == ()
    assert resultado.menciones == (
        Persona(
            "ALBA LUMARIA ZAFIRO",
            None,
            (origen,),
            "SIN_FICHA",
            conyuge="BRUNO TELURIO NEBULOSA",
            procedencia_conyuge=origen,
        ),
    )
    assert "BRUNO TELURIO NEBULOSA" in resultado["NOMBRE"]


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


_RENIEC_F12 = (
    "CUI: 90000011 - 5\n"
    "APELLIDO PATERNO  LUMARIA  APELLIDO MATERNO  ZAFIRO\n"
    "NOMBRES  ALBA\n"
    "DISTRITO DE NACIMIENTO  CERRO FICTICIO  PROVINCIA  OTRA\n"
    "ESTADO CIVIL  CASADA  SEXO  FEMENINO\n"
    "FECHA DE NACIMIENTO  03/07/1990  OTRO DATO  01/01/2000\n"
    "DIRECCIÓN  Av. Luna 12  PROVINCIA DE DOMICILIO  PROVINCIA FICTICIA\n"
    "DISTRITO DE DOMICILIO  Miraflores  DEPARTAMENTO DE DOMICILIO  LIMA"
)


def test_persona_f12_mantiene_constructor_posicional_y_campos_opcionales():
    origen = (Procedencia("ficticio.pdf", 2),)
    anterior = Persona("ALBA LUMARIA ZAFIRO", "90000011", origen)
    assert anterior.estado == "CONFIRMADA"
    assert (
        anterior.estado_civil,
        anterior.fecha_nacimiento,
        anterior.domicilio,
        anterior.distrito,
    ) == (
        None,
        None,
        None,
        None,
    )
    assert (
        Persona("ALBA LUMARIA ZAFIRO", "90000011", origen, "REVISION_MANUAL").estado
        == "REVISION_MANUAL"
    )
    ampliada = Persona(
        "ALBA LUMARIA ZAFIRO",
        "90000011",
        origen,
        "CONFIRMADA",
        "CASADO",
        date(1990, 7, 3),
        "Av. Luna 12",
        "Miraflores",
        origen[0],
        origen[0],
        origen[0],
        origen[0],
    )
    assert ampliada.procedencia_estado_civil == origen[0]
    assert ampliada.procedencia_fecha_nacimiento == origen[0]
    assert ampliada.procedencia_domicilio == origen[0]
    assert ampliada.procedencia_distrito == origen[0]


def test_reniec_ficticia_dos_columnas_aporta_cuatro_campos_con_procedencia():
    persona = catalogo({"reniec-ficticio.pdf": _RENIEC_F12}).personas[0]
    origen = Procedencia("reniec-ficticio.pdf", 1)
    assert (
        persona.estado_civil,
        persona.fecha_nacimiento,
        persona.domicilio,
        persona.distrito,
    ) == (
        "CASADO",
        date(1990, 7, 3),
        "Av. Luna 12",
        "Miraflores",
    )
    assert (
        persona.procedencia_estado_civil,
        persona.procedencia_fecha_nacimiento,
        persona.procedencia_domicilio,
        persona.procedencia_distrito,
    ) == (origen,) * 4


def test_pie_biometrico_no_es_estado_civil():
    pagina = (
        "INFORMACION PERSONAL\nPRIMER APELLIDO  LUMARIA\n"
        "SEGUNDO APELLIDO  ZAFIRO\nNOMBRES  ALBA\nDNI 90000011\n"
        "REGISTRO NACIONAL DE IDENTIFICACION Y ESTADO CIVIL"
    )
    assert (
        catalogo({"biometrica-ficticia.txt": pagina}).personas[0].estado_civil is None
    )


def test_campos_f12_no_se_leen_de_biometrica_ni_de_segunda_columna():
    biometrica = (
        "INFORMACION PERSONAL\nPRIMER APELLIDO  LUMARIA\n"
        "SEGUNDO APELLIDO  ZAFIRO\nNOMBRES  ALBA\nDNI 90000011\n"
        "ESTADO CIVIL  CASADA\nFECHA DE NACIMIENTO  03/07/1990\n"
        "DIRECCION  Av. Luna 12\nDISTRITO DE DOMICILIO  Miraflores"
    )
    persona = catalogo({"biometrica-ficticia.txt": biometrica}).personas[0]
    assert (
        persona.estado_civil,
        persona.fecha_nacimiento,
        persona.domicilio,
        persona.distrito,
    ) == (
        None,
        None,
        None,
        None,
    )
    segunda_columna = _RENIEC_F12.replace(
        "ESTADO CIVIL  CASADA  SEXO  FEMENINO",
        "OTRO CAMPO  ALGO  ESTADO CIVIL  CASADA",
    ).replace(
        "DISTRITO DE DOMICILIO  Miraflores",
        "OTRO CAMPO  ALGO  DISTRITO DE DOMICILIO  Miraflores",
    )
    persona = catalogo({"reniec-ficticio.pdf": segunda_columna}).personas[0]
    assert persona.estado_civil is None
    assert persona.distrito is None


def test_rotulo_reniec_con_dos_puntos_y_valor_en_celda_siguiente():
    pagina = _RENIEC_F12.replace("ESTADO CIVIL  CASADA", "ESTADO CIVIL:  CASADA")
    assert (
        catalogo({"reniec-ficticio.pdf": pagina}).personas[0].estado_civil == "CASADO"
    )


@pytest.mark.parametrize("valor", ["CASADA", "casado", "CASADO."])
def test_estado_civil_reniec_normaliza_genero_y_puntuacion(valor):
    pagina = _RENIEC_F12.replace("CASADA  SEXO", f"{valor}  SEXO")
    assert (
        catalogo({"reniec-ficticio.pdf": pagina}).personas[0].estado_civil == "CASADO"
    )


@pytest.mark.parametrize(
    "valor, esperado",
    [
        ("03/07/1990", date(1990, 7, 3)),
        ("03-07-1990", date(1990, 7, 3)),
        ("03/07/197б", None),
        ("31/02/1990", None),
    ],
)
def test_fecha_reniec_acepta_solo_lectura_inequivoca(valor, esperado):
    pagina = _RENIEC_F12.replace("03/07/1990  OTRO", f"{valor}  OTRO")
    persona = catalogo({"reniec-ficticio.pdf": pagina}).personas[0]
    assert persona.fecha_nacimiento == esperado
    assert (persona.procedencia_fecha_nacimiento is not None) == (esperado is not None)


def test_unificacion_conserva_cada_valor_y_su_procedencia():
    primera = catalogo({"reniec-ficticio.pdf": _RENIEC_F12}).personas[0]
    segunda = Persona(
        "ALBA LUMARIA ZAFIRO", "90000011", (Procedencia("anexo-ficticio.txt", 1),)
    )
    for orden in ((primera, segunda), (segunda, primera)):
        persona = unificar_personas(orden)[0]
        for campo in ("estado_civil", "fecha_nacimiento", "domicilio", "distrito"):
            assert getattr(persona, campo) == getattr(primera, campo)
            assert getattr(persona, f"procedencia_{campo}") == getattr(
                primera, f"procedencia_{campo}"
            )


def test_observaciones_historicas_identicas_con_misma_entrada_ficticia():
    fuentes = {"reniec-ficticio.pdf": _RENIEC_F12}
    borrador = "ALBA LUMARIA ZAFIRO, DE NACIONALIDAD PERUANA. DNI 90000022"
    cat = catalogo(fuentes)
    assert comparar_personas(cat, borrador) == (
        {
            "tipo": "DOCUMENTO_SIN_TITULAR",
            "nombre": "ALBA LUMARIA ZAFIRO",
            "documento_hallado": "90000022",
            "documento_esperado": None,
            "procedencias": (),
        },
    )
    assert revisar(cat, borrador, 88) == [
        "[DNI] «90000022» debe decir «90000011»   …ALBA LUMARIA ZAFIRO, DE NACIONALIDAD PERUANA. DNI 90000022",
        "[DNI] FALTA: «90000011» esta en las fuentes y no aparece en el destino",
    ]
    from nucleo.verificar import revisar_parrafos

    minuta = (
        "Este párrafo de minuta ficticia es suficientemente extenso y contiene "
        "texto notarial inventado para forzar una observación de comparación."
    )
    otro_borrador = (
        "Este párrafo de borrador ficticio es suficientemente extenso y contiene "
        "contenido notarial alternativo para forzar una diferencia visible."
    )
    assert revisar_parrafos([minuta], otro_borrador, 88) == [
        "[PARRAFO] falta o alterado (79.22%): ESTE PARRAFO DE MINUTA FICTICIA ES SUFICIENTEMENTE EXTENSO Y CONTIENE TEXTO NOTARIAL INVENTADO PARA …"
    ]


def test_conflicto_reniec_elige_emision_reciente_y_exige_revision():
    antigua = _RENIEC_F12.replace("ESTADO CIVIL  CASADA", "ESTADO CIVIL  SOLTERA")
    antigua += "\nFECHA DE EMISION  01/02/2024"
    reciente = _RENIEC_F12 + "\nFECHA DE EMISION  03/04/2025"
    for paginas in ((antigua, reciente), (reciente, antigua)):
        persona = catalogo({"reniec-ficticio.pdf": "\f".join(paginas)}).personas[0]
        assert persona.estado_civil == "CASADO"
        assert persona.estado == "REVISION_MANUAL"
        assert persona.procedencia_estado_civil.pagina == paginas.index(reciente) + 1


def test_emision_reciente_del_mismo_valor_no_se_pierde_en_tercera_ficha():
    primera = _RENIEC_F12 + "\nFECHA DE EMISION  01/02/2020"
    reciente = _RENIEC_F12 + "\nFECHA DE EMISION  01/02/2025"
    intermedia = (
        _RENIEC_F12.replace("CASADA", "SOLTERA") + "\nFECHA DE EMISION  01/02/2023"
    )
    persona = catalogo(
        {"reniec-ficticio.pdf": "\f".join((primera, reciente, intermedia))}
    ).personas[0]
    assert persona.estado_civil == "CASADO"
    assert persona.procedencia_estado_civil.pagina == 2
    assert persona.estado == "REVISION_MANUAL"


@pytest.mark.parametrize(
    ("civil", "frase", "tipos"),
    [
        (
            "CASADO",
            "ALBA LUMARIA ZAFIRO, peruana y propietaria.",
            ["CONYUGE_NO_MENCIONADO"],
        ),
        ("CASADO", "ALBA LUMARIA ZAFIRO, casada con BRUNO TELURIO NEBULOSA.", []),
        (
            "SOLTERO",
            "ALBA LUMARIA ZAFIRO, casada con BRUNO TELURIO NEBULOSA.",
            ["ESTADO_CIVIL_DISCREPANTE"],
        ),
        (None, "ALBA LUMARIA ZAFIRO, casada con BRUNO TELURIO NEBULOSA.", []),
    ],
)
def test_estado_civil_se_limita_a_clausula_personal(civil, frase, tipos):
    origen = Procedencia("reniec-ficticio.pdf", 1)
    persona = Persona(
        "ALBA LUMARIA ZAFIRO",
        "90000011",
        (origen,),
        estado_civil=civil,
        procedencia_estado_civil=origen if civil else None,
    )
    borrador = frase + "\nOTRA PERSONA, casada con alguien."
    obs = revisar_persona_ampliada(Catalogo((persona,)), borrador, date(2025, 1, 1))
    assert [fila["tipo"] for fila in obs] == tipos
    if obs:
        assert obs[0]["nombre"] == persona.nombre
        assert obs[0]["procedencia"] == origen


def test_persona_sin_documento_no_activa_regla_civil():
    origen = Procedencia("reniec-ficticio.pdf", 1)
    persona = Persona(
        "ALBA LUMARIA ZAFIRO",
        None,
        (origen,),
        "SIN_DOCUMENTO",
        estado_civil="CASADO",
        procedencia_estado_civil=origen,
    )
    assert (
        revisar_persona_ampliada(
            Catalogo((persona,)), "ALBA LUMARIA ZAFIRO, soltera.", date(2025, 1, 1)
        )
        == ()
    )


def test_edad_cumplida_a_fecha_inyectada():
    origen = Procedencia("reniec-ficticio.pdf", 1)
    for hoy, esperado in ((date(2025, 7, 2), 17), (date(2025, 7, 3), None)):
        persona = Persona(
            "ALBA LUMARIA ZAFIRO",
            "90000011",
            (origen,),
            fecha_nacimiento=date(2007, 7, 3),
            procedencia_fecha_nacimiento=origen,
        )
        obs = revisar_persona_ampliada(Catalogo((persona,)), "ALBA LUMARIA ZAFIRO", hoy)
        edades = [fila for fila in obs if fila["tipo"] == "MENOR_DE_EDAD"]
        assert [fila["edad"] for fila in edades] == ([esperado] if esperado else [])
        if edades:
            assert edades[0]["fecha_referencia"] == hoy


def test_domicilio_equivalente_y_ausente():
    origen = Procedencia("reniec-ficticio.pdf", 1)
    persona = Persona(
        "ALBA LUMARIA ZAFIRO",
        "90000011",
        (origen,),
        domicilio="Av. Lúna N° 12 Mz. A Lt. 3",
        procedencia_domicilio=origen,
    )
    fuente = Catalogo((persona,))
    presente = "ALBA LUMARIA ZAFIRO vive en Avenida Luna Manzana A Lote 3 Numero 12."
    ausente = "ALBA LUMARIA ZAFIRO vive en Calle Sol 8."
    assert revisar_persona_ampliada(fuente, presente, date(2025, 1, 1)) == ()
    obs = revisar_persona_ampliada(fuente, ausente, date(2025, 1, 1))
    assert [fila["tipo"] for fila in obs] == ["DOMICILIO_NO_ENCONTRADO"]
    assert obs[0]["procedencia"] == origen


@pytest.mark.parametrize(
    ("abreviado", "extendido"),
    [
        ("Av.", "Avenida"),
        ("Jr.", "Jirón"),
        ("Ca.", "Calle"),
        ("Psj.", "Pasaje"),
        ("Mz.", "Manzana"),
        ("Lt.", "Lote"),
        ("Urb.", "Urbanización"),
        ("AAHH", "Asentamiento Humano"),
        ("Dpto.", "Departamento"),
        ("Int.", "Interior"),
        ("N°", "Número"),
        ("S/N", "Sin Número"),
    ],
)
def test_domicilio_admite_equivalencias_cerradas(abreviado, extendido):
    origen = Procedencia("reniec-ficticio.pdf", 1)
    persona = Persona(
        "ALBA LUMARIA ZAFIRO",
        "90000011",
        (origen,),
        domicilio=f"{abreviado} Luna 12",
        procedencia_domicilio=origen,
    )
    borrador = f"ALBA LUMARIA ZAFIRO vive en {extendido} Luna 12."
    assert (
        revisar_persona_ampliada(Catalogo((persona,)), borrador, date(2025, 1, 1)) == ()
    )


def test_domicilio_de_otra_persona_no_satisface_fuente():
    origen = Procedencia("reniec-ficticio.pdf", 1)
    persona = Persona(
        "ALBA LUMARIA ZAFIRO",
        "90000011",
        (origen,),
        domicilio="Av. Luna 12",
        procedencia_domicilio=origen,
    )
    borrador = "ALBA LUMARIA ZAFIRO vive en Calle Sol 8.\nBRUNO TELURIO NEBULOSA vive en Av. Luna 12."
    obs = revisar_persona_ampliada(Catalogo((persona,)), borrador, date(2025, 1, 1))
    assert [fila["tipo"] for fila in obs] == ["DOMICILIO_NO_ENCONTRADO"]


# Paridad F13 (SC-005): salida capturada con el código previo a F13 sobre un
# legajo ficticio con ficha RENIEC, biométrica, declaración jurada con cónyuge,
# prosa, SUNARP y un documento suelto. No debe cambiar.
_LEGAJO_MINUTA = (
    "COMPARECEN ALBA LUMARIA ZAFIRO, DE NACIONALIDAD PERUANA, CON DNI 90000011, Y "
    "CLARA FICTELIA SOLARIA, DE NACIONALIDAD PERUANA, CON DNI 90000033, SOBRE LA "
    "PARTIDA N° 80000001 POR S/ 1,500.00\n"
    "DIANA ROCIO VENTORIA, DE NACIONALIDAD PERUANA, SIN DOCUMENTO A LA VISTA.\n"
    "LA VENDEDORA DECLARA QUE EL INMUEBLE FICTICIO SE ENTREGA LIBRE DE CARGAS, "
    "GRAVAMENES Y MEDIDAS JUDICIALES."
)
_LEGAJO = {
    "reniec-ficticio.pdf": (
        "CUI: 90000011 - 5\n"
        "APELLIDO PATERNO  LUMARIA  APELLIDO MATERNO  ZAFIRO\n"
        "NOMBRES  ALBA\n"
        "ESTADO CIVIL  CASADA  SEXO  FEMENINO\n"
        "\f"
        "INFORMACION PERSONAL\nPRIMER APELLIDO  TELURIO  SEGUNDO APELLIDO  NEBULOSA\n"
        "NOMBRES  BRUNO\nDNI 90000022"
    ),
    "declaracion-ficticia.txt": (
        "DECLARACION JURADA\nAPELLIDOS: LUMARIA ZAFIRO\nNOMBRES: ALBA\nDNI: 90000011\n"
        "NOMBRES Y APELLIDOS DEL CONYUGE: EMILIO SOLANO QUIMERA"
    ),
    "minuta-ficticia.txt": _LEGAJO_MINUTA,
    "sunarp-ficticio.txt": (
        "PARTIDA ELECTRONICA N° 80000001\nASIENTO B00001\n"
        "TELURIO NEBULOSA, BRUNO DE NACIONALIDAD PERUANA"
    ),
    "suelto-ficticio.txt": "DNI 90000044",
}
_LEGAJO_BORRADOR = (
    "ALBA LUMARIA ZAFIRA\nBRUNO TELURIO NEBULOSA\n"
    "COMPARECEN ALBA LUMARIA ZAFIRO, DE NACIONALIDAD PERUANA, CON DNI 90000011, Y "
    "CLARA FICTELIA SOLARIO, DE NACIONALIDAD PERUANA, CON DNI 90000039, SOBRE LA "
    "PARTIDA N° 80000002 POR S/ 1,500.00\n"
    "EMILIO SOLANO QUIMERA, DE NACIONALIDAD PERUANA, CONYUGE."
)


def test_paridad_capa_de_campos_con_legajo_ficticio():
    from nucleo.verificar import correspondencia, diagnostico, revisar_parrafos

    cat = catalogo(_LEGAJO)
    assert cat["NOMBRE"] == {
        "ALBA LUMARIA ZAFIRO",
        "BRUNO TELURIO NEBULOSA",
        "CLARA FICTELIA SOLARIA",
        "COMPARECEN ALBA LUMARIA ZAFIRO",
        "DIANA ROCIO VENTORIA",
        "EMILIO SOLANO QUIMERA",
    }
    assert cat["DNI"] == {"90000011", "90000022", "90000033", "90000044"}
    assert revisar(cat, _LEGAJO_BORRADOR, 88) == [
        "[NOMBRE] «CLARA FICTELIA SOLARIO» debe decir «CLARA FICTELIA SOLARIA»",
        "[NOMBRE] «ALBA LUMARIA ZAFIRA» debe decir «ALBA LUMARIA ZAFIRO»   (caratula)",
        "[DNI] «90000039» debe decir «90000033»   …Y CLARA FICTELIA SOLARIO, DE NACIONALIDAD PERUANA, CON DNI 90000039",
        "[PARTIDA] «80000002» debe decir «80000001»",
        "[NOMBRE] FALTA: «BRUNO TELURIO NEBULOSA» esta en las fuentes y no aparece en el destino",
        "[NOMBRE] FALTA: «CLARA FICTELIA SOLARIA» esta en las fuentes y no aparece en el destino",
        "[NOMBRE] FALTA: «COMPARECEN ALBA LUMARIA ZAFIRO» esta en las fuentes y no aparece en el destino",
        "[NOMBRE] FALTA: «DIANA ROCIO VENTORIA» esta en las fuentes y no aparece en el destino",
        "[DNI] FALTA: «90000022» esta en las fuentes y no aparece en el destino",
        "[DNI] FALTA: «90000033» esta en las fuentes y no aparece en el destino",
        "[DNI] FALTA: «90000044» esta en las fuentes y no aparece en el destino",
        "[PARTIDA] FALTA: «80000001» esta en las fuentes y no aparece en el destino",
    ]
    assert correspondencia(cat, _LEGAJO_BORRADOR) == (0.5, 1)
    assert diagnostico(_LEGAJO, _LEGAJO_BORRADOR) is None
    assert diagnostico(_LEGAJO, "SIN DATOS DNI 90000098 DNI 90000099") == (
        "El borrador no corresponde a estas fuentes: no comparte ningun dato "
        "identificatorio y trae 2 DNI distintos. Parece otro expediente o una "
        "plantilla."
    )
    assert revisar_parrafos([_LEGAJO_MINUTA], _LEGAJO_BORRADOR, 88) == [
        "[PARRAFO] falta o alterado (38.19%): LA VENDEDORA DECLARA QUE EL INMUEBLE "
        "FICTICIO SE ENTREGA LIBRE DE CARGAS, GRAVAMENES Y MEDIDAS JUDIC…"
    ]


def test_persona_f13_anade_campos_al_final_y_catalogo_menciones_vacias():
    origen = (Procedencia("ficticio.pdf", 1),)
    persona = Persona("ALBA LUMARIA ZAFIRO", "90000011", origen)
    assert persona == Persona("ALBA LUMARIA ZAFIRO", "90000011", origen, "CONFIRMADA")
    assert Persona._fields[-3:] == ("adjuntos", "conyuge", "procedencia_conyuge")
    assert (persona.adjuntos, persona.conyuge, persona.procedencia_conyuge) == (
        None,
        None,
        None,
    )
    assert Catalogo((persona,)).menciones == ()


def test_proyeccion_incluye_anclas_adjuntos_menciones_y_conyuges():
    origen = (Procedencia("ficticio.pdf", 1),)
    adjunto = Persona(
        "ALBA LUMARIA ZAFIRA", "90000011", origen, conyuge="EMILIO SOLANO"
    )
    ancla = Persona(
        "ALBA LUMARIA ZAFIRO",
        "90000011",
        origen,
        adjuntos=(adjunto,),
        conyuge="EMILIO SOLANO QUIMERA",
    )
    mencion = Persona("DIANA ROCIO VENTORIA", "90000044", origen, "SIN_FICHA")
    cat = Catalogo((ancla,), menciones=(mencion,))
    assert cat["NOMBRE"] == {
        "ALBA LUMARIA ZAFIRO",
        "ALBA LUMARIA ZAFIRA",
        "EMILIO SOLANO",
        "EMILIO SOLANO QUIMERA",
        "DIANA ROCIO VENTORIA",
    }
    assert cat["DNI"] == {"90000011", "90000044"}


def _reniec(documento, nombres, paterno, materno):
    return (
        f"CUI: {documento} - 5\n"
        f"APELLIDO PATERNO  {paterno}  APELLIDO MATERNO  {materno}\n"
        f"NOMBRES  {nombres}"
    )


def _biometrica(documento, nombres, primero, segundo):
    return (
        "INFORMACION PERSONAL\n"
        f"PRIMER APELLIDO  {primero}  SEGUNDO APELLIDO  {segundo}\n"
        f"NOMBRES  {nombres}\nDNI {documento}"
    )


_ALBA = _reniec("90000011", "ALBA", "LUMARIA", "ZAFIRO")


def test_prosa_sola_no_crea_persona_sino_mencion_sin_ficha():
    resultado = catalogo(
        {
            "minuta-ficticia.txt": "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000011"
        }
    )

    assert resultado.personas == ()
    assert resultado.menciones == (
        Persona(
            "ALBA ZAFIRO LUMARIA",
            "90000011",
            (Procedencia("minuta-ficticia.txt", 1),),
            "SIN_FICHA",
        ),
    )
    assert resultado["NOMBRE"] == {"ALBA ZAFIRO LUMARIA"}


def test_reniec_y_biometrica_de_la_misma_persona_son_un_ancla():
    resultado = catalogo(
        {
            "reniec-ficticio.pdf": _ALBA,
            "biometrica-ficticia.txt": _biometrica(
                "90000011", "ALBA", "LUMARIA", "ZAFIRO"
            ),
        }
    )

    assert [(p.nombre, p.documento, p.estado) for p in resultado.personas] == [
        ("ALBA LUMARIA ZAFIRO", "90000011", "CONFIRMADA")
    ]
    assert len(resultado.personas[0].procedencias) == 2
    assert resultado.menciones == ()


def test_prosa_con_documento_del_ancla_se_adjunta_sin_conflicto():
    resultado = catalogo(
        {
            "reniec-ficticio.pdf": _ALBA,
            "minuta-ficticia.txt": "ALBA LUMARIA ZAFIRA, DE NACIONALIDAD PERUANA. DNI 90000011",
        }
    )

    (ancla,) = resultado.personas
    assert ancla.estado == "CONFIRMADA"
    assert ancla.nombre == "ALBA LUMARIA ZAFIRO"
    assert ancla.adjuntos == (
        Persona(
            "ALBA LUMARIA ZAFIRA",
            "90000011",
            (Procedencia("minuta-ficticia.txt", 1),),
        ),
    )
    assert resultado.menciones == ()
    assert {"ALBA LUMARIA ZAFIRO", "ALBA LUMARIA ZAFIRA"} <= resultado["NOMBRE"]


def test_nombre_solo_se_adjunta_a_ancla_unica_con_la_misma_clave():
    prosa = "ALBA LUMARIA ZAFIRO, DE NACIONALIDAD PERUANA."
    unica = catalogo({"reniec-ficticio.pdf": _ALBA, "minuta-ficticia.txt": prosa})
    assert [a.nombre for a in unica.personas[0].adjuntos] == ["ALBA LUMARIA ZAFIRO"]
    assert unica.menciones == ()

    homonimas = catalogo(
        {
            "reniec-ficticio.pdf": _ALBA
            + "\f"
            + _reniec("90000022", "ALBA", "LUMARIA", "ZAFIRO"),
            "minuta-ficticia.txt": prosa,
        }
    )
    assert len(homonimas.personas) == 2
    assert all(p.adjuntos is None for p in homonimas.personas)
    assert [(m.nombre, m.estado) for m in homonimas.menciones] == [
        ("ALBA LUMARIA ZAFIRO", "SIN_FICHA")
    ]


def test_documento_sin_ancla_nunca_se_pega_por_nombre():
    resultado = catalogo(
        {
            "reniec-ficticio.pdf": _ALBA,
            "minuta-ficticia.txt": "ALBA LUMARIA ZAFIRO, DE NACIONALIDAD PERUANA. DNI 90000099",
        }
    )

    assert resultado.personas[0].adjuntos is None
    assert [(m.nombre, m.documento, m.estado) for m in resultado.menciones] == [
        ("ALBA LUMARIA ZAFIRO", "90000099", "SIN_FICHA")
    ]


def test_conflictos_solo_entre_anclas():
    distintos = catalogo(
        {
            "reniec-ficticio.pdf": _ALBA
            + "\f"
            + _reniec("90000022", "ALBA", "LUMARIA", "ZAFIRO")
        }
    )
    assert [(p.documento, p.estado) for p in distintos.personas] == [
        ("90000011", "CONFIRMADA"),
        ("90000022", "CONFIRMADA"),
    ]

    cruzados = catalogo(
        {
            "reniec-ficticio.pdf": _ALBA
            + "\f"
            + _reniec("90000011", "BRUNO", "TELURIO", "NEBULOSA")
        }
    )
    assert [(p.nombre, p.estado) for p in cruzados.personas] == [
        ("ALBA LUMARIA ZAFIRO", "REVISION_MANUAL")
    ]

    antigua = (
        _RENIEC_F12.replace("CASADA", "SOLTERA") + "\nFECHA DE EMISION  01/02/2024"
    )
    reciente = _RENIEC_F12 + "\nFECHA DE EMISION  03/04/2025"
    (ancla,) = catalogo({"reniec-ficticio.pdf": f"{antigua}\f{reciente}"}).personas
    assert (ancla.estado_civil, ancla.estado) == ("CASADO", "REVISION_MANUAL")


def test_documento_suelto_se_pega_a_la_ficha_unificada():
    resultado = catalogo(
        {
            "reniec-ficticio.pdf": _ALBA
            + "\f"
            + _reniec("90000011", "BRUNO", "TELURIO", "NEBULOSA"),
            "suelto-ficticio.txt": "DNI 90000011",
        }
    )

    (ancla,) = resultado.personas
    assert [(a.nombre, a.documento) for a in ancla.adjuntos] == [
        ("BRUNO TELURIO NEBULOSA", "90000011"),
        (None, "90000011"),
    ]
    assert resultado.menciones == ()


def test_ficha_reniec_sin_documento_legible_es_mencion():
    ilegible = _ALBA.replace("CUI: 90000011 - 5", "CUI: 9000O011")
    resultado = catalogo({"reniec-ficticio.pdf": ilegible})

    assert resultado.personas == ()
    assert [(m.nombre, m.documento, m.estado) for m in resultado.menciones] == [
        ("ALBA LUMARIA ZAFIRO", None, "SIN_FICHA")
    ]


def _declaracion(conyuge, documento="90000011"):
    dni = f"DNI: {documento}\n" if documento else ""
    return (
        "DECLARACION JURADA\nAPELLIDOS: LUMARIA ZAFIRO\nNOMBRES: ALBA\n"
        f"{dni}NOMBRES Y APELLIDOS DEL CONYUGE: {conyuge}"
    )


def test_conyuge_de_declaracion_jurada_se_adjunta_al_ancla():
    resultado = catalogo(
        {
            "reniec-ficticio.pdf": _ALBA,
            "declaracion-ficticia.txt": _declaracion("EMILIO SOLANO QUIMERA"),
        }
    )

    origen = Procedencia("declaracion-ficticia.txt", 1)
    (ancla,) = resultado.personas
    assert (ancla.conyuge, ancla.procedencia_conyuge) == (
        "EMILIO SOLANO QUIMERA",
        origen,
    )
    assert ancla.adjuntos == (
        Persona(
            "ALBA LUMARIA ZAFIRO",
            "90000011",
            (origen,),
            conyuge="EMILIO SOLANO QUIMERA",
            procedencia_conyuge=origen,
        ),
    )
    assert ancla.estado == "CONFIRMADA"
    assert resultado.menciones == ()
    assert "EMILIO SOLANO QUIMERA" in resultado["NOMBRE"]


def test_declarante_sin_documento_se_pega_por_nombre_unico():
    resultado = catalogo(
        {
            "reniec-ficticio.pdf": _ALBA,
            "declaracion-ficticia.txt": _declaracion("EMILIO SOLANO QUIMERA", None),
        }
    )

    (ancla,) = resultado.personas
    assert ancla.conyuge == "EMILIO SOLANO QUIMERA"
    assert [(a.nombre, a.documento) for a in ancla.adjuntos] == [
        ("ALBA LUMARIA ZAFIRO", None)
    ]
    assert resultado.menciones == ()


def test_menciones_del_mismo_declarante_con_conyuges_distintos_no_se_fusionan():
    resultado = catalogo(
        {
            "declaracion-ficticia.txt": _declaracion("EMILIO SOLANO QUIMERA")
            + "\f"
            + _declaracion("FABIO RIVORIA TELMO")
        }
    )

    assert [m.conyuge for m in resultado.menciones] == [
        "EMILIO SOLANO QUIMERA",
        "FABIO RIVORIA TELMO",
    ]
    assert {m.estado for m in resultado.menciones} == {"SIN_FICHA"}


def test_dos_declaraciones_con_conyuges_distintos_en_el_mismo_ancla():
    resultado = catalogo(
        {
            "reniec-ficticio.pdf": _ALBA,
            "declaracion-ficticia.txt": _declaracion("EMILIO SOLANO QUIMERA")
            + "\f"
            + _declaracion("FABIO RIVORIA TELMO"),
        }
    )

    (ancla,) = resultado.personas
    assert ancla.estado == "CONFIRMADA"
    assert ancla.conyuge == "EMILIO SOLANO QUIMERA"
    assert ancla.procedencia_conyuge == Procedencia("declaracion-ficticia.txt", 1)
    assert [a.conyuge for a in ancla.adjuntos] == [
        "EMILIO SOLANO QUIMERA",
        "FABIO RIVORIA TELMO",
    ]
    assert {"EMILIO SOLANO QUIMERA", "FABIO RIVORIA TELMO"} <= resultado["NOMBRE"]


def test_conyuge_sin_declarante_identificado_es_mencion_propia():
    resultado = catalogo(
        {
            "declaracion-ficticia.txt": (
                "DECLARACION JURADA\n"
                "NOMBRES Y APELLIDOS DEL CONYUGE: EMILIO SOLANO QUIMERA"
            )
        }
    )

    origen = Procedencia("declaracion-ficticia.txt", 1)
    assert resultado.personas == ()
    assert resultado.menciones == (
        Persona(
            None,
            None,
            (origen,),
            "SIN_FICHA",
            conyuge="EMILIO SOLANO QUIMERA",
            procedencia_conyuge=origen,
        ),
    )
    assert resultado["NOMBRE"] == {"EMILIO SOLANO QUIMERA"}


# F15: una persona por DNI entre fichas oficiales. Nombres inventados.
_OLGA = _reniec("90000051", "OLGA MIRELA", "TARANCO", "VELIZ")
_OLGA_MINUTA = (
    "COMPARECE OLGA MIRELA TARANCO VELIZ CON DNI 90000051 SOBRE LA PARTIDA "
    "N° 80000005 POR S/ 2,000.00\nLA COMPRADORA DECLARA QUE EL INMUEBLE "
    "FICTICIO SE ENTREGA SIN CARGAS NI GRAVAMENES CONOCIDOS."
)


def _olga_con_biometrica(nombres, primero="TARANCO", segundo="VELIZ"):
    return catalogo(
        {
            "biometrica-ficticia.txt": _biometrica(
                "90000051", nombres, primero, segundo
            ),
            "reniec-ficticio.pdf": _OLGA,
        }
    )


def test_paridad_capa_de_campos_con_fichas_duplicadas_por_ocr():
    from nucleo.verificar import correspondencia, diagnostico, revisar_parrafos

    legajo = {
        "biometrica-ficticia.txt": _biometrica(
            "90000051", "OLGAIMIRELA", "TARANCO", "VELIZ"
        ),
        "reniec-ficticio.pdf": _OLGA,
        "minuta-ficticia.txt": _OLGA_MINUTA,
    }
    borrador = (
        "OLGA MIRELA TARANCO VELIS\nCOMPARECE OLGA MIRELA TARANCO VELIZ CON DNI "
        "90000015 SOBRE LA PARTIDA N° 80000005 POR S/ 2,000.00"
    )
    cat = catalogo(legajo)
    assert cat["NOMBRE"] == {"OLGA MIRELA TARANCO VELIZ", "OLGAIMIRELA TARANCO VELIZ"}
    assert cat["DNI"] == {"90000051"}
    assert revisar(cat, borrador, 88) == [
        "[NOMBRE] «OLGA MIRELA TARANCO VELIS» debe decir «OLGA MIRELA TARANCO VELIZ»   (caratula)",
        "[DNI] «90000015» debe decir «90000051»   … TARANCO VELIS COMPARECE OLGA MIRELA TARANCO VELIZ CON DNI 90000015",
        "[NOMBRE] FALTA: «OLGAIMIRELA TARANCO VELIZ» esta en las fuentes y no aparece en el destino",
        "[DNI] FALTA: «90000051» esta en las fuentes y no aparece en el destino",
    ]
    assert correspondencia(cat, borrador) == (2 / 3, 1)
    assert diagnostico(legajo, borrador) is None
    assert revisar_parrafos([_OLGA_MINUTA], borrador, 88) == [
        "[PARRAFO] falta o alterado (44.78%): LA COMPRADORA DECLARA QUE EL INMUEBLE "
        "FICTICIO SE ENTREGA SIN CARGAS NI GRAVAMENES CONOCIDOS.…"
    ]


def test_mismo_dni_con_espacio_leido_como_letra_es_una_persona_confirmada():
    resultado = _olga_con_biometrica("OLGAIMIRELA")

    (ancla,) = resultado.personas
    assert (ancla.nombre, ancla.documento, ancla.estado) == (
        "OLGA MIRELA TARANCO VELIZ",
        "90000051",
        "CONFIRMADA",
    )
    assert ancla.adjuntos == (
        Persona(
            "OLGAIMIRELA TARANCO VELIZ",
            "90000051",
            (Procedencia("biometrica-ficticia.txt", 1),),
        ),
    )
    assert set(ancla.procedencias) == {
        Procedencia("biometrica-ficticia.txt", 1),
        Procedencia("reniec-ficticio.pdf", 1),
    }
    assert resultado["NOMBRE"] == {
        "OLGA MIRELA TARANCO VELIZ",
        "OLGAIMIRELA TARANCO VELIZ",
    }


def test_variante_de_ficha_sigue_atrayendo_prosa_sin_documento():
    resultado = catalogo(
        {
            "biometrica-ficticia.txt": _biometrica(
                "90000051", "OLGAIMIRELA", "TARANCO", "VELIZ"
            ),
            "reniec-ficticio.pdf": _OLGA,
            "minuta-ficticia.txt": "OLGAIMIRELA TARANCO VELIZ, DE NACIONALIDAD PERUANA.",
        }
    )

    (ancla,) = resultado.personas
    assert [a.procedencias[0].fuente for a in ancla.adjuntos] == [
        "biometrica-ficticia.txt",
        "minuta-ficticia.txt",
    ]
    assert resultado.menciones == ()


@pytest.mark.parametrize(
    ("nombres", "primero", "segundo", "estado"),
    [
        ("OLGA MIRELA", "TARANKO", "VELIS", "CONFIRMADA"),
        ("OLGA MIRELO", "TARANKO", "VELIS", "REVISION_MANUAL"),
        ("OLGA MIRELA", "TARANCO", "VEL", "REVISION_MANUAL"),
    ],
    ids=["dos-ediciones", "tres-ediciones", "truncado"],
)
def test_mismo_dni_decide_estado_por_distancia_del_nombre(
    nombres, primero, segundo, estado
):
    (ancla,) = _olga_con_biometrica(nombres, primero, segundo).personas
    assert (ancla.nombre, ancla.estado) == ("OLGA MIRELA TARANCO VELIZ", estado)
    assert [a.nombre for a in ancla.adjuntos] == [f"{nombres} {primero} {segundo}"]


def test_dos_reniec_mismo_dni_manda_la_emision_mas_reciente():
    antigua = _OLGA + "\nFECHA DE EMISION  01/02/2024"
    reciente = (
        _reniec("90000051", "OLGA MIRELA", "TARANKO", "VELIZ")
        + "\nFECHA DE EMISION  03/04/2025"
    )
    for paginas in ((antigua, reciente), (reciente, antigua)):
        (ancla,) = catalogo({"reniec-ficticio.pdf": "\f".join(paginas)}).personas
        assert (ancla.nombre, ancla.estado) == (
            "OLGA MIRELA TARANKO VELIZ",
            "CONFIRMADA",
        )
        assert [a.nombre for a in ancla.adjuntos] == ["OLGA MIRELA TARANCO VELIZ"]


def test_dos_reniec_mismo_dni_sin_fecha_manda_la_primera_pagina():
    otra = _reniec("90000051", "OLGA MIRELA", "TARANKO", "VELIZ")
    (ancla,) = catalogo({"reniec-ficticio.pdf": f"{otra}\f{_OLGA}"}).personas
    assert ancla.nombre == "OLGA MIRELA TARANKO VELIZ"
    assert [a.procedencias for a in ancla.adjuntos] == [
        (Procedencia("reniec-ficticio.pdf", 2),)
    ]


def test_dni_distinto_y_mismo_nombre_siguen_siendo_dos_anclas():
    resultado = catalogo(
        {
            "reniec-ficticio.pdf": _OLGA,
            "biometrica-ficticia.txt": _biometrica(
                "90000062", "OLGA MIRELA", "TARANCO", "VELIZ"
            ),
        }
    )
    assert [(p.documento, p.estado, p.adjuntos) for p in resultado.personas] == [
        ("90000051", "CONFIRMADA", None),
        ("90000062", "CONFIRMADA", None),
    ]
