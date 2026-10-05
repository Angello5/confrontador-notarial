"""Lectura del borrador con datos ficticios: sin ficha, DNI de 8 dígitos,
estado civil de cada persona, domicilio en cuadros y oficina registral."""

from datetime import date

from nucleo.verificar import (
    Catalogo,
    Persona,
    Procedencia,
    catalogo,
    revisar,
    revisar_persona_ampliada,
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
