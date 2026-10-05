"""F35 con textos inventados: partidas en todos sus formatos y empresa contra la ficha RUC."""

from nucleo.correccion import correcciones
from nucleo.verificar import catalogo, fichas_ruc, revisar

FICHA_REPORTE = """SUNAT
Reporte de Ficha RUC  Lima, 01/01/2026
PANADERIA LOS OLIVOS DEL NORTE E.I.R.L.
20123456789
Estado del Contribuyente  ACTIVO
Domicilio Fiscal
Tipo y Nombre Zona  URB. LAS FLORES
Tipo y Nombre Vía  AV. LOS PINOS
Nro  123
"""

FICHA_CIR = """SUNAT
FICHA RUC : 20987654321
CONSTRUCTORA EL ALBA SOCIEDAD COMERCIAL DE
RESPONSABILIDAD LIMITADA
Número de Transacción : 12345
Domicilio Fiscal
Tipo y Nombre Vía  JR. LAS GARDENIAS
Nro  540
Mz
Otras Referencias  2DO PISO OF.NRO 04
"""


def _observaciones(fuentes, borrador, campo, **opciones):
    salidas = revisar(catalogo(fuentes), borrador, 90, **opciones)
    return [salida for salida in salidas if salida.startswith(f"[{campo}]")]


def test_partida_con_numero_dos_puntos_o_registral_se_compara():
    fuente = {"recaudo-ficticio.txt": "PARTIDA ELECTRONICA N° 11223344 DE LIMA."}
    borrador = (
        "INSCRITO EN LA PARTIDA ELECTRONICA NUMERO 1122334 DEL REGISTRO. "
        "PARTIDA: 11223344. PARTIDA REGISTRAL 11223345."
    )
    assert _observaciones(fuente, borrador, "PARTIDA") == [
        "[PARTIDA] «1122334» debe decir «11223344»",
        "[PARTIDA] «11223345» debe decir «11223344»",
    ]


def test_partida_con_prefijo_de_letra_se_compara():
    fuente = {"recaudo-ficticio.txt": "PARTIDA N° P01234567 DEL REGISTRO DE PREDIOS."}
    assert _observaciones(fuente, "PARTIDA ELECTRONICA N°P01234576", "PARTIDA") == [
        "[PARTIDA] «P01234576» debe decir «P01234567»",
        "[PARTIDA] FALTA: «P01234567» esta en las fuentes y no aparece en el destino",
    ]
    assert _observaciones(fuente, "PARTIDA N° P01234567", "PARTIDA") == []


def test_partida_ausente_solo_se_exige_si_esta_en_la_minuta():
    minuta = "EL PODER CORRE EN LA PARTIDA N° 11223344."
    fuentes = {
        "minuta-ficticia.txt": minuta,
        "recaudo-ficticio.txt": "ANTECEDENTE: FICHA N° 99887766.",
    }
    assert _observaciones(
        fuentes, "SIN PARTIDAS.", "PARTIDA", minutas={"minuta-ficticia.txt": minuta}
    ) == ["[PARTIDA] FALTA: «11223344» esta en las fuentes y no aparece en el destino"]


def test_razon_social_distinta_de_la_ficha_ruc():
    fuente = {"recaudo-ficticio.txt": FICHA_REPORTE}
    borrador = (
        "Y DE LA OTRA PARTE: PANADERIA LOS OLIVOS DEL NARTE E.I.R.L..- CON REGISTRO "
        "UNICO DE CONTRIBUYENTE NUMERO 20123456789. INTERVIENE OTRA FINANCIERA S.A."
    )
    assert _observaciones(fuente, borrador, "RAZON_SOCIAL") == [
        "[RAZON_SOCIAL] «PANADERIA LOS OLIVOS DEL NARTE» debe decir "
        "«PANADERIA LOS OLIVOS DEL NORTE»   (ficha RUC)"
    ]
    for correcto in (
        "PANADERIA LOS OLIVOS DEL NORTE E.I.R.L.",
        "PANADERIA LOS OLIVOS DEL NORTE EMPRESA INDIVIDUAL DE RESPONSABILIDAD LIMITADA",
    ):
        assert _observaciones(fuente, correcto, "RAZON_SOCIAL") == []


def test_razon_social_de_una_palabra_no_se_confunde_con_otra_palabra():
    ficha = FICHA_REPORTE.replace(
        "PANADERIA LOS OLIVOS DEL NORTE E.I.R.L.", "TRANSFERIX S.A.C."
    )
    borrador = "TRANSFERIX S.A.C. SE OBLIGA A TRANSFERIR EL BIEN."
    assert (
        _observaciones({"recaudo-ficticio.txt": ficha}, borrador, "RAZON_SOCIAL") == []
    )


def test_domicilio_fiscal_con_numero_distinto_de_la_ficha_ruc():
    fuente = {"recaudo-ficticio.txt": FICHA_CIR}
    borrador = (
        "CONSTRUCTORA EL ALBA SOCIEDAD COMERCIAL DE RESPONSABILIDAD LIMITADA.- CON "
        "REGISTRO UNICO DE CONTRIBUYENTE NUMERO 20987654321, CON DOMICILIO LEGAL EN "
        "JIRON LAS GARDENIAS NUMERO 54 - OFICINA # 04, DISTRITO DE LIMA."
    )
    assert _observaciones(fuente, borrador, "DOMICILIO_FISCAL") == [
        "[DOMICILIO_FISCAL] «JIRON LAS GARDENIAS NUMERO 54 - OFICINA # 04» debe decir "
        "«JR. LAS GARDENIAS NRO 540 2DO PISO OF.NRO 04»   (ficha RUC)"
    ]
    assert _observaciones(fuente, borrador, "RAZON_SOCIAL") == []
    correcto = borrador.replace("NUMERO 54 - OFICINA # 04", "NUMERO 540, OFICINA 04")
    assert _observaciones(fuente, correcto, "DOMICILIO_FISCAL") == []


def test_solo_la_razon_social_entra_en_la_correccion_automatica():
    fuentes = {"recaudo-ficticio.txt": FICHA_REPORTE}
    salidas = [
        "[RAZON_SOCIAL] «PANADERIA LOS OLIVOS DEL NARTE» debe decir "
        "«PANADERIA LOS OLIVOS DEL NORTE»   (ficha RUC)",
        "[DOMICILIO_FISCAL] «AVENIDA LOS PINOS NUMERO 12» debe decir "
        "«AV. LOS PINOS NRO 123»   (ficha RUC)",
    ]
    assert [c["campo"] for c in correcciones(salidas, fuentes)] == ["RAZON_SOCIAL"]


def test_ficha_ruc_sin_razon_social_legible_no_aporta_empresa():
    assert fichas_ruc("FICHA RUC : 20987654321\nNúmero de Transacción : 1\n") == []
