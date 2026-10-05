"""F41: concordancia de género con el sexo de RENIEC, con datos ficticios."""

from datetime import date

from nucleo.verificar import (
    Catalogo,
    Pagina,
    Persona,
    Procedencia,
    _campos_reniec,
    revisar_persona_ampliada,
)

HOY = date(2025, 1, 1)
ORIGEN = Procedencia("reniec-ficticio.pdf", 1)


def _persona(nombre, documento, sexo):
    return Persona(nombre, documento, (ORIGEN,), sexo=sexo, procedencia_sexo=ORIGEN)


def _genero(observaciones):
    return [
        (o["nombre"], o["hallado"], o["esperado"])
        for o in observaciones
        if o["tipo"] == "GENERO"
    ]


def test_sexo_se_lee_de_la_consulta_reniec():
    pagina = "Sexo: {}\nFecha de Nacimiento: 01/01/1980"
    leido = _campos_reniec(Pagina("reniec-ficticio.pdf", 2, pagina.format("FEMENINO")))
    vacio = _campos_reniec(Pagina("reniec-ficticio.pdf", 2, pagina.format("")))
    assert (leido["sexo"], leido["procedencia_sexo"]) == (
        "FEMENINO",
        Procedencia("reniec-ficticio.pdf", 2),
    )
    assert (vacio["sexo"], vacio["procedencia_sexo"]) == (None, None)


def test_comparecencia_en_el_otro_genero():
    ana = _persona("ANA LUCIA PEREZ ROJAS", "90000021", "FEMENINO")
    linea = (
        "EL SEÑOR ANA LUCIA PEREZ ROJAS, DE NACIONALIDAD PERUANA, DE ESTADO CIVIL "
        "CASADO, DANDO FE DE HABERSE IDENTIFICADO CON DNI N° 90000021, DOMICILIADO "
        "EN JR. LUNA 1, Y LUIS RAMOS DIAZ, SOLTERO."
    )
    # «haberse identificado» es invariable; el «SOLTERO» es de otra persona
    assert _genero(revisar_persona_ampliada(Catalogo((ana,)), linea, HOY)) == [
        ("ANA LUCIA PEREZ ROJAS", "SEÑOR", "FEMENINO («SEÑORA»)"),
        ("ANA LUCIA PEREZ ROJAS", "CASADO", "FEMENINO («CASADA»)"),
        ("ANA LUCIA PEREZ ROJAS", "DOMICILIADO", "FEMENINO («DOMICILIADA»)"),
    ]


def test_formulas_del_notario_con_un_solo_otorgante():
    luis = _persona("LUIS RAMOS DIAZ", "90000031", "MASCULINO")
    borrador = (
        "LUIS RAMOS DIAZ, DE ESTADO CIVIL SOLTERO, CON DNI N° 90000031.\n"
        "EL NOTARIO VERIFICA QUE LA OTORGANTE PRESENTO LA DECLARACION SOBRE "
        "BENEFICIARIO FINAL, SIENDO LA BENEFICIARIA FINAL LA MISMA OTORGANTE, "
        "QUEDANDO ADVERTIDA. EL CLIENTE DECLARA HABER SIDO INFORMADO. SE INSTRUYO "
        "AL OTORGANTE."
    )
    assert _genero(revisar_persona_ampliada(Catalogo((luis,)), borrador, HOY)) == [
        ("LUIS RAMOS DIAZ", "LA OTORGANTE", "MASCULINO («EL OTORGANTE»)"),
        ("LUIS RAMOS DIAZ", "LA MISMA OTORGANTE", "MASCULINO («EL MISMO OTORGANTE»)"),
        ("LUIS RAMOS DIAZ", "QUEDANDO ADVERTIDA", "MASCULINO («QUEDANDO ADVERTIDO»)"),
        (
            "LUIS RAMOS DIAZ",
            "LA BENEFICIARIA FINAL",
            "MASCULINO («EL BENEFICIARIO FINAL»)",
        ),
    ]


def test_formulas_no_se_revisan_con_comparecientes_de_ambos_sexos():
    luis = _persona("LUIS RAMOS DIAZ", "90000031", "MASCULINO")
    ana = _persona("ANA LUCIA PEREZ ROJAS", "90000021", "FEMENINO")
    sin_sexo = _persona("ALBA LUMARIA ZAFIRO", "90000041", None)
    borrador = (
        "LUIS RAMOS DIAZ, CON DNI N° 90000031. ANA LUCIA PEREZ ROJAS, CON DNI N° "
        "90000021. ALBA LUMARIA ZAFIRO, CON DNI N° 90000041.\nQUEDANDO ADVERTIDA."
    )
    assert _genero(revisar_persona_ampliada(Catalogo((luis, ana)), borrador, HOY)) == []
    # uno sin sexo legible: no se puede decidir
    assert (
        _genero(revisar_persona_ampliada(Catalogo((luis, sin_sexo)), borrador, HOY))
        == []
    )
