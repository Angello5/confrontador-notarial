"""Lectura del borrador con datos ficticios: sin ficha, DNI de 8 dígitos,
estado civil de cada persona, domicilio en cuadros y oficina registral."""

from datetime import date

from nucleo.verificar import (
    Catalogo,
    Persona,
    Procedencia,
    catalogo,
    comparar_personas,
    revisar,
    revisar_persona_ampliada,
    sin_ficha_por_persona,
)

HOY = date(2025, 1, 1)
ORIGEN = Procedencia("reniec-ficticio.pdf", 1)


def _reniec(documento, nombres_, paterno, materno):
    return (
        f"CUI: {documento} - 5\n"
        f"APELLIDO PATERNO  {paterno}  APELLIDO MATERNO  {materno}\n"
        f"NOMBRES  {nombres_}"
    )


def _de(prefijos, salidas):
    return [s for s in salidas if s.startswith(prefijos)]


def test_persona_sin_ficha_en_los_recaudos_es_aviso_medio():
    fuentes = {
        "reniec-ficticio.pdf": _reniec("90000021", "ANA LUCIA", "PEREZ", "ROJAS")
    }
    borrador = (
        "ANA LUCIA PEREZ ROJAS, DE NACIONALIDAD PERUANA, CON DNI N° 90000021. "
        "PEDRO PABLO SOTO VERA, DE NACIONALIDAD PERUANA, CON DNI N° 48172635."
    )
    salidas = _de(
        ("[NOMBRE]", "[DNI]", "[SIN_FICHA]"), revisar(catalogo(fuentes), borrador, 90)
    )
    assert (
        salidas[0]
        == "[SIN_FICHA] «PEDRO PABLO SOTO VERA» sin ficha RENIEC en los recaudos"
    )
    assert salidas[1].startswith(
        "[SIN_FICHA] «48172635» sin ficha RENIEC en los recaudos"
    )
    assert len(salidas) == 2


def test_sin_ficha_muestra_como_escribe_la_minuta_el_nombre():
    """F39: sin ficha no hay «debe decir», pero se ve lo que dice la minuta."""
    fuentes = {
        "reniec-ficticio.pdf": _reniec("90000021", "ANA LUCIA", "PEREZ", "ROJAS")
    }
    minuta = (
        "ANA LUCIA PEREZ ROJAS CON DNI 90000021 Y PEDRO PABLO SOTO VERA "
        "CON DNI 48172635 CELEBRAN EL CONTRATO FICTICIO."
    )
    borrador = (
        "ANA LUCIA PEREZ ROJAS, DE NACIONALIDAD PERUANA, CON DNI N° 90000021. "
        "PEDRO PABLO {} VERA, DE NACIONALIDAD PERUANA, CON DNI N° 48172635."
    )
    minutas = {"minuta-ficticia.docx": minuta}

    def sin_ficha(apellido):
        salidas = revisar(
            catalogo(fuentes), borrador.format(apellido), 90, None, None, minutas
        )
        return _de(("[SIN_FICHA] «PEDRO",), salidas)

    assert sin_ficha("ZOTO") == [
        "[SIN_FICHA] «PEDRO PABLO ZOTO VERA» sin ficha RENIEC en los recaudos; "
        "la minuta dice «PEDRO PABLO SOTO VERA»"
    ]
    # igual que en la minuta: solo el aviso
    assert sin_ficha("SOTO") == [
        "[SIN_FICHA] «PEDRO PABLO SOTO VERA» sin ficha RENIEC en los recaudos"
    ]


def test_dni_que_no_tiene_ocho_digitos():
    fuentes = {
        "reniec-ficticio.pdf": _reniec("90000021", "ANA LUCIA", "PEREZ", "ROJAS")
    }
    borrador = "PEDRO PABLO SOTO VERA, DE NACIONALIDAD PERUANA, CON DNI N° 900007."
    salidas = _de(("[DNI]",), revisar(catalogo(fuentes), borrador, 90))
    assert salidas[0].startswith("[DNI] «900007» debe tener 8 dígitos")


def test_estado_civil_es_el_que_sigue_al_nombre_de_la_persona():
    persona = Persona(
        "ANA LUCIA PEREZ ROJAS",
        "90000021",
        (ORIGEN,),
        estado_civil="CASADO",
        procedencia_estado_civil=ORIGEN,
    )
    linea = (
        "EL SEÑOR CARLOS SOTO VERA, DE ESTADO CIVIL SOLTERO, Y LA SEÑORA ANA LUCIA "
        "PEREZ ROJAS, CON DNI N° 90000099, DE ESTADO CIVIL CASADA CON LUIS RAMOS DIAZ."
    )
    assert revisar_persona_ampliada(Catalogo((persona,)), linea, HOY) == ()


def test_conyuge_presentada_en_la_clausula_del_otro_esta_casada():
    persona = Persona(
        "ANA LUCIA PEREZ ROJAS",
        "90000021",
        (ORIGEN,),
        estado_civil="CASADO",
        procedencia_estado_civil=ORIGEN,
    )
    linea = (
        "EL SEÑOR CARLOS SOTO VERA, DE ESTADO CIVIL SOLTERO; EL SEÑOR LUIS RAMOS "
        "DIAZ, DE ESTADO CIVIL CASADO CON LA SEÑORA ANA LUCIA PEREZ ROJAS, CON DNI "
        "N° 90000021, DE OCUPACION INDEPENDIENTE."
    )
    assert revisar_persona_ampliada(Catalogo((persona,)), linea, HOY) == ()


def test_domicilio_en_la_fila_siguiente_de_un_cuadro():
    persona = Persona(
        "ALBA LUMARIA ZAFIRO",
        "90000011",
        (ORIGEN,),
        domicilio="JR. LUNA 12",
        procedencia_domicilio=ORIGEN,
    )
    cuadro = (
        "DEPOSITARIO\nNOMBRE ALBA LUMARIA ZAFIRO SOLTERA\nDNI 90000011\n"
        "DOMICILIO JR. LUNA 12 LIMA\n"
    )
    assert revisar_persona_ampliada(Catalogo((persona,)), cuadro, HOY) == ()


def test_oficina_pegada_a_la_linea_siguiente_del_certificado():
    fuente = (
        "OFICINA REGISTRAL LIMA\nSUPERINTENDENCIA NACIONAL DE LOS REGISTROS PUBLICOS"
    )
    borrador = "INSCRITA EN LA OFICINA REGISTRAL DE LIMA."
    salidas = revisar(catalogo({"certificado-ficticio.pdf": fuente}), borrador, 90)
    assert _de(("[DATO_REGISTRAL]",), salidas) == []


def test_enie_de_la_ficha_escaneada_es_aviso_de_marca_de_agua():
    fuentes = {
        "reniec-ficticio.pdf": _reniec("90000021", "LUIS DAÑIEL", "ROJAS", "PAZ")
    }
    borrador = "LUIS DANIEL ROJAS PAZ, DE NACIONALIDAD PERUANA, CON DNI N° 90000021."
    minuta = {"minuta.txt": "LUIS DANIEL ROJAS PAZ, DE NACIONALIDAD PERUANA."}
    salidas = revisar(catalogo(fuentes), borrador, 90, minutas=minuta)
    assert _de(("[NOMBRE", "[SIN_FICHA]"), salidas) == [
        "[NOMBRE_MARCA_AGUA] «LUIS DANIEL ROJAS PAZ» posible Ñ por marca de agua; "
        "verifique el DNI"
    ]
    # Si la minuta trae la Ñ, el borrador que la omite sigue en error.
    con_enie = {"minuta.txt": "LUIS DAÑIEL ROJAS PAZ, DE NACIONALIDAD PERUANA."}
    salidas = revisar(catalogo(fuentes), borrador, 90, minutas=con_enie)
    assert (
        "[NOMBRE] «LUIS DANIEL ROJAS PAZ» debe decir «LUIS DAÑIEL ROJAS PAZ»" in salidas
    )


def test_casado_que_interviene_sin_conyuge_por_bien_propio_es_aviso():
    persona = Persona(
        "LUIS RAMOS DIAZ",
        "90000031",
        (ORIGEN,),
        estado_civil="CASADO",
        procedencia_estado_civil=ORIGEN,
    )
    linea = (
        "LUIS RAMOS DIAZ, CON DNI N° 90000031, DE ESTADO CIVIL CASADO, SIN LA "
        "INTERVENCION DE SU CONYUGE POR SER BIEN PROPIO."
    )
    observaciones = revisar_persona_ampliada(Catalogo((persona,)), linea, HOY)
    assert [fila["tipo"] for fila in observaciones] == ["CONYUGE_BIEN_PROPIO"]


def test_persona_sin_ficha_es_un_solo_aviso():
    """F51: el representante sin ficha deja un aviso, no tres observaciones."""
    fuentes = {
        "reniec-ficticio.pdf": _reniec("90000021", "ANA LUCIA", "PEREZ", "ROJAS")
    }
    borrador = (
        "ANA LUCIA PEREZ ROJAS, DE NACIONALIDAD PERUANA, CON DNI N° 90000021.\n"
        "INVERSIONES FICTICIAS S.A.C., DEBIDAMENTE REPRESENTADA POR PEDRO PABLO "
        "SOTO VERA, DE NACIONALIDAD PERUANA, IDENTIFICADO CON DNI N° 48172635.\n"
        "PEDRO PABLO SOTO VERA, DE NACIONALIDAD PERUANA, CON DNI N° 48172635."
    )
    cat = catalogo(fuentes)
    reglas, personas = sin_ficha_por_persona(
        revisar(cat, borrador, 90), comparar_personas(cat, borrador)
    )
    assert _de(("[SIN_FICHA]",), reglas) == [
        "[SIN_FICHA] «PEDRO PABLO SOTO VERA» sin ficha RENIEC en los recaudos"
    ]
    assert personas == ()


def test_dni_ajeno_de_una_persona_con_ficha_sigue_siendo_alta():
    """F51: con ficha, el DNI que no es suyo sigue como documento sin titular."""
    fuentes = {
        "reniec-ficticio.pdf": _reniec("90000021", "ANA LUCIA", "PEREZ", "ROJAS")
    }
    borrador = "ANA LUCIA PEREZ ROJAS, DE NACIONALIDAD PERUANA, CON DNI N° 48172635."
    cat = catalogo(fuentes)
    reglas = revisar(cat, borrador, 90)
    personas = comparar_personas(cat, borrador)
    assert sin_ficha_por_persona(reglas, personas) == (reglas, personas)
    assert [p["tipo"] for p in personas] == ["DOCUMENTO_SIN_TITULAR"]
