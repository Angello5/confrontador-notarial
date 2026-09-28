"""F22: RUC y direcciones por aparición en el borrador (datos ficticios)."""

from datetime import date

from nucleo.verificar import (
    Catalogo,
    Persona,
    Procedencia,
    catalogo,
    nombres_exigibles,
    revisar,
    revisar_persona_ampliada,
)

_ORIGEN = (Procedencia("ficticio.pdf", 1),)
_MINUTA = (
    "LA EMPRESA ALFA FICTICIA S.A.C., CON R.U.C. N° 20000000001, CON DOMICILIO "
    "EN AV. LOS OLIVOS FICTICIOS 123, DISTRITO DE SAN FICTICIO, PROVINCIA DE LIMA."
)
_FICHA = (
    "REGISTRO UNICO DE CONTRIBUYENTES: 10900000112\n"
    "DOMICILIO FISCAL:  JR. LAS GARZAS IMAGINARIAS 456\n"
    "DISTRITO DE DOMICILIO  MIRAFLORES\n"
    "SEÑALA COMO DOMICILIO EL INDICADO EN LA INTRODUCCION"
)


def _discrepancias(cat, borrador, campo):
    return [o for o in revisar(cat, borrador, 88) if o.startswith(f"[{campo}] «")]


# --- RUC -----------------------------------------------------------------


def test_catalogo_lee_ruc_rotulados_con_prefijo_valido():
    sisgen = "CONSULTA REALIZADA\nCOINCIDENCIAS\nRUC 20000000009"
    cat = catalogo(
        {
            "minuta.docx": _MINUTA,
            "ficha.pdf": _FICHA,
            "otros.pdf": "RUC 30000000001. RUC 2000000000. RUC: 20000000003",
            "sisgen.pdf": sisgen,
        }
    )
    assert cat["RUC"] == {"20000000001", "10900000112", "20000000003"}


def test_ruc_alterado_se_observa_aunque_haya_una_copia_correcta():
    cat = catalogo({"minuta.docx": _MINUTA})
    borrador = (
        "ALFA FICTICIA S.A.C., CON RUC N° 20000000001. EN LA CLAUSULA TERCERA LA "
        "EMPRESA CON R.U.C. 20000000007 DECLARA."
    )
    assert _discrepancias(cat, borrador, "RUC") == [
        "[RUC] «20000000007» debe decir «20000000001»"
    ]


def test_ruc_de_longitud_incorrecta_o_ajeno():
    cat = catalogo({"minuta.docx": _MINUTA})
    borrador = "CON RUC 2000000001 Y CON REGISTRO UNICO DE CONTRIBUYENTE 55555555555"
    assert _discrepancias(cat, borrador, "RUC") == [
        "[RUC] «2000000001» debe decir «20000000001»",
        "[RUC] «55555555555» no coincide con ninguna fuente",
    ]


def test_ruc_correcto_o_sin_rotulo_no_genera_observacion():
    cat = catalogo({"minuta.docx": _MINUTA})
    borrador = "CON RUC N° 20000000001. CUENTA 20000000007."
    assert [o for o in revisar(cat, borrador, 88) if o.startswith("[RUC]")] == []


def test_ruc_falta_solo_si_viene_de_la_minuta():
    cat = catalogo({"minuta.docx": _MINUTA, "ficha.pdf": _FICHA})
    exigibles = nombres_exigibles(cat, [_MINUTA])
    borrador = "TEXTO SIN RUC."
    assert [o for o in revisar(cat, borrador, 88, exigibles) if "[RUC]" in o] == [
        "[RUC] FALTA: «20000000001» esta en las fuentes y no aparece en el destino"
    ]
    assert len([o for o in revisar(cat, borrador, 88) if "[RUC]" in o]) == 2


# --- DIRECCION -----------------------------------------------------------


def test_catalogo_lee_direcciones_rotuladas():
    cat = catalogo({"minuta.docx": _MINUTA, "ficha.pdf": _FICHA})
    assert cat["DIRECCION"] == {
        "AV. LOS OLIVOS FICTICIOS 123",
        "JR. LAS GARZAS IMAGINARIAS 456",
    }


def test_direccion_alterada_se_observa_por_aparicion():
    cat = catalogo({"minuta.docx": _MINUTA})
    borrador = (
        "ALFA FICTICIA S.A.C., CON DOMICILIO EN AV. LOS OLIVOS FICTICIOS 123, "
        "DISTRITO DE SAN FICTICIO.\n"
        "LA EMPRESA DOMICILIADA EN AVENIDA LOS OLIVOS FICTICIOS 132, PROVINCIA DE LIMA."
    )
    assert _discrepancias(cat, borrador, "DIRECCION") == [
        "[DIRECCION] «AVENIDA LOS OLIVOS FICTICIOS 132» debe decir "
        "«AV. LOS OLIVOS FICTICIOS 123»"
    ]


def test_direccion_equivalente_o_sin_parecida_no_se_observa():
    cat = catalogo({"minuta.docx": _MINUTA, "ficha.pdf": _FICHA})
    borrador = (
        "CON DOMICILIO EN AVENIDA LOS OLIVOS FICTICIOS N° 123. EL COMPRADOR, "
        "DOMICILIADO EN CALLE TOTALMENTE DISTINTA 9; Y LA EMPRESA CON DOMICILIO "
        "LEGAL EN JIRON LAS GARZAS IMAGINARIAS 456, DISTRITO DE MIRAFLORES."
    )
    assert _discrepancias(cat, borrador, "DIRECCION") == []


def test_sin_ruc_ni_direcciones_revisar_no_cambia_con_dict_legado():
    legado = {"NOMBRE": set(), "DNI": set(), "PARTIDA": set(), "MONTO": set()}
    borrador = "CON RUC 20000000001, CON DOMICILIO EN AV. LUNA 12."
    assert revisar(legado, borrador, 88) == [
        "[RUC] «20000000001» no coincide con ninguna fuente"
    ]


def test_domicilio_no_encontrado_no_duplica_la_observacion_de_direccion():
    persona = Persona(
        "ALBA LUMARIA ZAFIRO",
        "90000011",
        _ORIGEN,
        domicilio="Av. Luna 12",
        procedencia_domicilio=_ORIGEN[0],
    )
    cat = Catalogo((persona,))
    borrador = (
        "ALBA LUMARIA ZAFIRO CON DNI 90000011, CON DOMICILIO EN AV. LUNA 13, "
        "DISTRITO DE SAN FICTICIO."
    )
    assert _discrepancias(cat, borrador, "DIRECCION") == [
        "[DIRECCION] «AV. LUNA 13» debe decir «AV. LUNA 12»"
    ]
    assert revisar_persona_ampliada(cat, borrador, date(2025, 1, 1)) == ()


def test_adaptador_interpreta_direccion():
    from expedientes.services import adaptar_observaciones_regla

    cat = catalogo({"minuta.docx": _MINUTA})
    borrador = "PRIMERA LINEA\nCON DOMICILIO EN AV. LOS OLIVOS FICTICIOS 132, DISTRITO"
    (fila,) = adaptar_observaciones_regla(
        _discrepancias(cat, borrador, "DIRECCION"), borrador
    )
    assert (fila["campo"], fila["hallado"], fila["esperado"]) == (
        "DIRECCION",
        "AV. LOS OLIVOS FICTICIOS 132",
        "AV. LOS OLIVOS FICTICIOS 123",
    )
    assert fila["ubicacion"]["linea"] == 2
