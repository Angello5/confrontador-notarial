"""F74: DNI del cónyuge y registro de otra entidad. Solo datos ficticios."""

from nucleo import correccion
from nucleo.verificar import (
    _nombres_de_pagina,
    _registrales_observados,
    catalogo,
    datos_registrales,
    norm,
)


def _registrales(fuente, borrador):
    pares = [(clase, valor) for clase, valor, _ in datos_registrales(norm(fuente))]
    return _registrales_observados(pares, norm(borrador))


def _asignados(texto):
    return [
        (persona.nombre, persona.documento)
        for persona in catalogo({"borrador": texto})._registros()
    ]


BOLETA = "BOLETA INFORMATIVA\nREGISTRO DE PROPIEDAD VEHICULAR\n"
ACTA_EMPRESA = (
    "TRANSFERENCIA QUE OTORGA EMPRESA FICTICIA S.A.C., INSCRITA EN LA PARTIDA "
    "ELECTRONICA N° 70000001 DEL REGISTRO DE PERSONAS JURIDICAS DE LIMA."
)


def test_registro_de_personas_juridicas_no_se_cambia_por_el_del_vehiculo():
    observaciones = _registrales(BOLETA, ACTA_EMPRESA)

    assert observaciones == []
    assert correccion.correcciones(observaciones, {"boleta.pdf": BOLETA}) == []


def test_registro_del_mismo_grupo_se_sigue_observando():
    fuente = "INSCRITO EN EL REGISTRO DE PREDIOS."
    borrador = "INSCRITO EN EL REGISTRO DE PROPIEDAD VEHICULAR."

    assert _registrales(fuente, borrador) == [
        "[DATO_REGISTRAL] «REGISTRO DE PROPIEDAD VEHICULAR» debe decir "
        "«REGISTRO DE PREDIOS»"
    ]


def test_el_conyuge_no_se_queda_con_el_dni_de_quien_comparece():
    texto = (
        "COMPARECEN: DON ALBERTO FICTICIO RAMOS.- CASADO CON DOÑA BEATRIZ INVENTADA "
        "SOTO, IDENTIFICADO CON DOCUMENTO NACIONAL DE IDENTIDAD NUMERO 90000001, "
        "DOMICILIADO EN LIMA."
    )

    assert ("BEATRIZ INVENTADA SOTO", "90000001") not in _asignados(texto)


def test_con_el_compareciente_en_la_linea_el_dni_es_suyo():
    texto = (
        "DON ALBERTO FICTICIO RAMOS, DE NACIONALIDAD PERUANA, CASADO CON DOÑA BEATRIZ "
        "INVENTADA SOTO, IDENTIFICADO CON DOCUMENTO NACIONAL DE IDENTIDAD NUMERO "
        "90000001, DOMICILIADO EN LIMA."
    )

    asignados = _asignados(texto)

    assert ("ALBERTO FICTICIO RAMOS", "90000001") in asignados
    assert ("BEATRIZ INVENTADA SOTO", "90000001") not in asignados


def test_el_conyuge_que_comparece_conserva_su_propio_dni():
    texto = (
        "DOÑA BEATRIZ INVENTADA SOTO, DE NACIONALIDAD PERUANA, CASADA CON DON ALBERTO "
        "FICTICIO RAMOS, IDENTIFICADA CON DOCUMENTO NACIONAL DE IDENTIDAD NUMERO "
        "90000002, DOMICILIADA EN LIMA."
    )

    asignados = _asignados(texto)

    assert ("BEATRIZ INVENTADA SOTO", "90000002") in asignados
    assert ("ALBERTO FICTICIO RAMOS", "90000002") not in asignados


def test_nombre_de_la_prosa_no_se_pega_a_lo_que_la_precede():
    # La coma de «APELLIDOS, NOMBRES» no existe en esta prosa: lo de antes de
    # la coma es una cláusula o una ocupación, nunca apellidos.
    minuta = (
        "UNA DE CONTRATO DE MUTUO CON GARANTIA HIPOTECARIA QUE OTORGA DE UNA "
        "PARTE LA SOCIEDAD CONYUGAL, ALFREDO ZAFIRO LUMARIA DE NACIONALIDAD "
        "PERUANA, IDENTIFICADO CON DNI 90000001, EMPRESARIO, Y SANDRA BRUNA "
        "NEBULOSA DE NACIONALIDAD PERUANA, IDENTIFICADA CON DNI 90000002."
    )
    nombres = _nombres_de_pagina(minuta, "PROSA", False)
    assert "ALFREDO ZAFIRO LUMARIA" in nombres
    assert "SANDRA BRUNA NEBULOSA" in nombres
    assert not [n for n in nombres if "SOCIEDAD" in n or n.startswith("Y ")]
    assert not [n for n in nombres if n.endswith("EMPRESARIO")]


def test_apellidos_coma_nombres_sigue_reordenandose():
    texto = "ZAFIRO LUMARIA, ALBA DE NACIONALIDAD PERUANA"
    assert "ALBA ZAFIRO LUMARIA" in _nombres_de_pagina(texto, "PROSA", False)


def test_nombre_tras_la_otra_parte_y_con_guion_se_reconoce():
    # «LOS MUTUANTES Y DE LA OTRA PARTE <nombre>» y «<nombre>. - DE NACIONALIDAD»
    # son formas habituales de presentar a una parte: el nombre es solo el nombre.
    minuta = (
        "ADELANTE SE LE DENOMINARA LOS MUTUANTES Y DE LA OTRA PARTE ALBA ZAFIRO "
        "LUMARIA, DE NACIONALIDAD PERUANA, IDENTIFICADA CON DNI 90000003."
    )
    assert "ALBA ZAFIRO LUMARIA" in _nombres_de_pagina(minuta, "PROSA", False)
    guion = (
        "DE LA OTRA PARTE:\nBRUNO TELURIA NEBULOSA. - DE NACIONALIDAD PERUANA, SOLTERO"
    )
    assert "BRUNO TELURIA NEBULOSA" in _nombres_de_pagina(guion, "PROSA", False)
