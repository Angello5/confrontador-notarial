"""F19: errores del borrador fuera de la comparecencia (datos ficticios)."""

from nucleo.verificar import Catalogo, Persona, Procedencia, revisar

_ORIGEN = (Procedencia("ficticio.pdf", 1),)
_CAT = Catalogo(
    (
        Persona("ALBA LUMARIA ZAFIRO", "90000011", _ORIGEN),
        Persona("BRUNO TELURIO NEBULOSA", "90000022", _ORIGEN),
    )
)


def _discrepancias(cat, borrador, campo):
    return [o for o in revisar(cat, borrador, 88) if o.startswith(f"[{campo}] «")]


# --- A: DNI de longitud incorrecta tras rótulo -------------------------------


def test_dni_con_un_digito_de_menos_tras_rotulo_largo():
    (obs,) = _discrepancias(
        _CAT, "IDENTIFICADA CON DOCUMENTO NACIONAL DE IDENTIDAD NUMERO 9000011.", "DNI"
    )
    assert obs.startswith("[DNI] «9000011» debe decir «90000011»")


def test_dni_con_digito_de_mas_y_rotulo_corto():
    (obs,) = _discrepancias(_CAT, "CON DNI N°900000222, DOMICILIADO", "DNI")
    assert obs.startswith("[DNI] «900000222» debe decir «90000022»")


def test_dni_lejano_no_coincide_con_ninguna_fuente():
    (obs,) = _discrepancias(_CAT, "CON D.N.I. NRO 123456", "DNI")
    assert obs.startswith("[DNI] «123456» no coincide con ninguna fuente")


def test_numero_suelto_sin_rotulo_no_es_dni():
    assert _discrepancias(_CAT, "EN UN PLAZO DE 9000011 SEGUNDOS", "DNI") == []


def test_dni_correcto_no_genera_observacion():
    borrador = "CON D.N.I. N° 90000011 Y DNI NRO 90000022"
    assert _discrepancias(_CAT, borrador, "DNI") == []
    assert not any(o.startswith("[DNI] FALTA") for o in revisar(_CAT, borrador, 88))


# --- B: nombre mal escrito en cualquier cláusula -----------------------------


def test_nombre_mal_escrito_en_representacion():
    borrador = (
        "LA SOCIEDAD REPRESENTADA POR ALBA LUMARIA ZAFIRO Y EN REPRESENTACION DE "
        "BRUNO TELURIA NEBULOSA, SEGUN PODER INSCRITO."
    )
    assert _discrepancias(_CAT, borrador, "NOMBRE") == [
        "[NOMBRE] «BRUNO TELURIA NEBULOSA» debe decir «BRUNO TELURIO NEBULOSA»"
    ]


def test_nombre_mal_escrito_aunque_aparezca_bien_en_otra_clausula():
    borrador = (
        "BRUNO TELURIO NEBULOSA, DE NACIONALIDAD PERUANA. ALBA LUMARIA ZAFIRO, "
        "DE NACIONALIDAD PERUANA. EN REPRESENTACION DE BRUNO TELURIA NEBULOSA."
    )
    assert _discrepancias(_CAT, borrador, "NOMBRE") == [
        "[NOMBRE] «BRUNO TELURIA NEBULOSA» debe decir «BRUNO TELURIO NEBULOSA»"
    ]


def test_nombres_identicos_no_generan_observacion():
    borrador = "REPRESENTADA POR ALBA LUMARIA ZAFIRO Y POR BRUNO TELURIO NEBULOSA."
    assert _discrepancias(_CAT, borrador, "NOMBRE") == []


def test_dos_personas_parecidas_una_exacta_no_genera_observacion():
    cat = Catalogo(
        (
            Persona("CARLOS RUBIO MENDEZ", "90000033", _ORIGEN),
            Persona("CARLOS RUBIO MENDES", "90000044", _ORIGEN),
        )
    )
    borrador = "EN REPRESENTACION DE CARLOS RUBIO MENDEZ, SEGUN PODER."
    assert _discrepancias(cat, borrador, "NOMBRE") == []


def test_ventana_ya_observada_por_nacionalidad_no_se_repite():
    borrador = "BRUNO TELURIA NEBULOSA, DE NACIONALIDAD PERUANA, Y ALBA LUMARIA ZAFIRO."
    assert _discrepancias(_CAT, borrador, "NOMBRE") == [
        "[NOMBRE] «BRUNO TELURIA NEBULOSA» debe decir «BRUNO TELURIO NEBULOSA»"
    ]


# --- C: número en letras distinto de su cifra --------------------------------

_VACIO = Catalogo(())


def test_letras_distintas_de_la_cifra():
    assert _discrepancias(
        _VACIO, "EN EL PLAZO DE TREINTA Y SIETE (36) MESES.", "NUMERO_EN_LETRAS"
    ) == ["[NUMERO_EN_LETRAS] «TREINTA Y SIETE (36)» debe decir «36»"]


def test_cifra_distinta_de_las_letras():
    assert _discrepancias(
        _VACIO, "EN EL PLAZO DE TREINTA Y SEIS (37) MESES.", "NUMERO_EN_LETRAS"
    ) == ["[NUMERO_EN_LETRAS] «TREINTA Y SEIS (37)» debe decir «37»"]


def test_palabra_numerica_mal_escrita():
    assert _discrepancias(
        _VACIO, "EN EL PLAZO DE TREINTA Y SEIZ (36) MESES.", "NUMERO_EN_LETRAS"
    ) == ["[NUMERO_EN_LETRAS] «TREINTA Y SEIZ (36)» debe decir «36»"]


def test_palabra_numerica_corta_mal_escrita():
    assert _discrepancias(
        _VACIO, "EN EL PLAZO DE TREINTA Y SES (36) MESES.", "NUMERO_EN_LETRAS"
    ) == ["[NUMERO_EN_LETRAS] «TREINTA Y SES (36)» debe decir «36»"]


def test_palabras_cortas_comunes_no_se_toman_por_numeros():
    assert (
        _discrepancias(
            _VACIO, "A LOS DIAS DEL MES (12) Y SUS ANEXOS (3).", "NUMERO_EN_LETRAS"
        )
        == []
    )


def test_centimos_distintos():
    assert _discrepancias(
        _VACIO, "LA SUMA DE MIL QUINIENTOS Y 50/100 (S/ 1,500.00).", "NUMERO_EN_LETRAS"
    ) == [
        "[NUMERO_EN_LETRAS] «MIL QUINIENTOS Y 50/100 (S/ 1,500.00)» debe decir «1,500.00»"
    ]


def test_letras_y_cifra_coincidentes_no_generan_observacion():
    borrador = (
        "EN EL PLAZO DE TREINTA Y SEIS (36) MESES. LA SUMA DE MIL QUINIENTOS Y "
        "00/100 (1,500.00). EL AÑO DOS MIL VEINTISEIS (2026). CIENTO VEINTITRES MIL "
        "CUATROCIENTOS CINCUENTA Y SEIS (123,456). UN MIL (1,000.00). "
        "DOSCIENTAS UNA (201). CERO (0). CLAUSULA PRIMERA (1). ASIENTO (2)."
    )
    assert _discrepancias(_VACIO, borrador, "NUMERO_EN_LETRAS") == []


def test_adaptador_interpreta_las_nuevas_observaciones():
    from expedientes.services import adaptar_observaciones_regla

    borrador = "PRIMERA LINEA\nEN EL PLAZO DE TREINTA Y SIETE (36) MESES."
    (fila,) = adaptar_observaciones_regla(revisar(_VACIO, borrador, 88), borrador)
    assert (fila["campo"], fila["hallado"], fila["esperado"]) == (
        "NUMERO_EN_LETRAS",
        "TREINTA Y SIETE (36)",
        "36",
    )
    assert fila["ubicacion"]["linea"] == 2


def test_signos_del_ocr_en_el_nombre_de_la_fuente_no_son_error():
    cat = Catalogo((Persona("ALBA LUMARIA ZAFIRO:", "90000011", _ORIGEN),))
    borrador = "COMPARECE ALBA LUMARIA ZAFIRO, CON DNI N° 90000011."
    assert _discrepancias(cat, borrador, "NOMBRE") == []
