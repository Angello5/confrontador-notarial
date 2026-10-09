"""F43: transferencia vehicular contra la boleta informativa y los cheques.

Solo datos ficticios.
"""

from nucleo import vehicular

# Boleta informativa leída por filas (capa de texto del PDF o OCR).
BOLETA = (
    "COPIA INFORMATIVA\n"
    "BOLETA INFORMATIVA\n"
    "Datos del Propietario\n"
    "Nombre  : EMPRESA FICTICIA DEMO S.A.C.  PARTIDA\n"
    "Dirección  : CALLE FICTICIA 100 - LIMA - LIMA  70000009\n"
    "Características del Vehículo  (VEHÍCULO EN CIRCULACION)\n"
    "Placa  : QWE123  OFICINA LIMA\n"
    "Tipo Uso  : Particular  N° Partida  : 70000001\n"
    "Categoría  : M1  Color 3  : ##########\n"
    "Carrocería  : SEDAN  N° Motor  : MOT0000001  N° Ejes  : 2\n"
    "Marca  : MARCAFICTA  Tipo Combus  : GASOLINA  N° Ruedas  : 4\n"
    "Modelo  : MODELOX  Pot. Motor  : 100@5000  Longitud  : 4.00 mt\n"
    "Año Mod  : 2020  N° Cilindros  : 4  Ancho  : 1.70 mt\n"
    "Año Fab  : 2019  Cilindrada  : 1.500 L  Altura  : 1.50 mt\n"
    "N° Serie  : 9ZZZZ00ZZZ0000001  Peso Bruto  : 1.60 tn\n"
    "N° de VIN  : 9ZZZZ00ZZZ0000001  Carga Útil  : 0.40 tn\n"
    "Color 1  : AZUL FICTICIO  N° Asientos  : 5\n"
    "Color 2  : ##########  N° Pasajer.  : 4\n"
)

# Cheque leído por OCR: el monto con punto de miles es ruido habitual.
CHEQUE = (
    "Interbank\n"
    "N° 00000001  003  041  0000000000  12\n"
    "pague a\n"
    "la orden de:  EMPRESA FICTICIA DEMO S.A.C.\n"
    "DOCE MIL TRESCIENTOS CUARENTA Y CINCO Y 00/100 SOLES\n"
    "CHEQUE DE GERENCIA\n"
    "NO NEGOCIABLE\n"
    "*****12.345.00\n"
    "Soles\n"
)

BORRADOR = (
    "ACTA DE TRANSFERENCIA DE VEHICULO AUTOMOTOR POR COMPRA-VENTA\n"
    "CELEBRADA ENTRE: EMPRESA FICTICIA DEMO S.A.C., COMO LA TRANSFERENTE.\n"
    "PRIMERO: EL TRANSFERENTE MANIFIESTA SU VOLUNTAD DE TRANSFERIR EL VEHICULO:\n"
    "PLACA: QWE123, CONFORME A LOS DATOS QUE OBRAN EN LA PARTIDA REGISTRAL: "
    "70000001 DE LA OFICINA REGISTRAL DE: LIMA.\n"
    "SEGUNDO: EL PRECIO ES DE S/ 12,345.00 (DOCE MIL TRESCIENTOS CUARENTA Y "
    "CINCO Y 00/100 SOLES) QUE SE CANCELA CON CHEQUE DE GERENCIA N° 00000001.\n"
)


def _fuentes(**extra):
    return {"boleta-ficticia.pdf": BOLETA, "cheque-ficticio.jpg": CHEQUE, **extra}


def test_lee_la_boleta_por_rotulos():
    boleta = vehicular.boletas({"boleta-ficticia.pdf": BOLETA})[0]
    assert boleta["PLACA"] == "QWE123"
    assert boleta["PARTIDA"] == "70000001"
    assert boleta["MARCA"] == "MARCAFICTA"
    assert boleta["SERIE"] == "9ZZZZ00ZZZ0000001"
    assert boleta["MOTOR"] == "MOT0000001"
    assert boleta["COLOR"] == "AZUL FICTICIO"
    assert boleta["PROPIETARIO"] == ["EMPRESA FICTICIA DEMO S.A.C."]
    assert "COLOR 2" not in boleta  # «#####» no es un dato


def test_un_texto_sin_boleta_no_aporta_vehiculo():
    assert (
        vehicular.boletas({"dni-ficticio.pdf": "DOCUMENTO NACIONAL DE IDENTIDAD"}) == []
    )


def test_borrador_correcto_no_tiene_observaciones():
    assert vehicular.revisar(_fuentes(), BORRADOR) == []


def test_placa_distinta():
    obs = vehicular.revisar(
        _fuentes(), BORRADOR.replace("PLACA: QWE123", "PLACA: QWE128")
    )
    assert obs == ["[PLACA] «QWE128» debe decir «QWE123»"]


def test_placa_con_guion_es_la_misma():
    assert vehicular.revisar(_fuentes(), BORRADOR.replace("QWE123", "QWE-123")) == []


def test_placa_ausente():
    obs = vehicular.revisar(_fuentes(), BORRADOR.replace("PLACA: QWE123, ", ""))
    assert obs == [
        "[PLACA] FALTA: «QWE123» esta en las fuentes y no aparece en el destino"
    ]


def test_partida_del_vehiculo_distinta():
    obs = vehicular.revisar(_fuentes(), BORRADOR.replace("70000001", "70000002"))
    assert obs == ["[PARTIDA] «70000002» debe decir «70000001»"]


def test_caracteristica_solo_si_el_borrador_la_menciona():
    con_marca = BORRADOR.replace("PLACA: QWE123,", "PLACA: QWE123, MARCA: MARCAFICTO,")
    assert vehicular.revisar(_fuentes(), con_marca) == [
        "[VEHICULO] «MARCAFICTO» debe decir «MARCAFICTA»"
    ]
    con_serie = BORRADOR.replace(
        "PLACA: QWE123,", "PLACA: QWE123, SERIE: 9ZZZZ00ZZZ0000007,"
    )
    assert vehicular.revisar(_fuentes(), con_serie) == [
        "[VEHICULO] «9ZZZZ00ZZZ0000007» debe decir «9ZZZZ00ZZZ0000001»"
    ]


def test_transferente_distinto_del_propietario():
    obs = vehicular.revisar(
        _fuentes(),
        BORRADOR.replace(
            "ENTRE: EMPRESA FICTICIA DEMO", "ENTRE: EMPRESA FICTICIA DEMA"
        ),
    )
    assert obs == [
        "[PROPIETARIO] «EMPRESA FICTICIA DEMA S.A.C.» debe decir "
        "«EMPRESA FICTICIA DEMO S.A.C.»"
    ]


def test_monto_del_cheque_ausente():
    obs = vehicular.revisar(_fuentes(), BORRADOR.replace("12,345.00", "12,354.00"))
    assert obs == [
        "[CHEQUE] FALTA: «S/ 12,345.00» esta en las fuentes y no aparece en el destino"
    ]


def test_del_cheque_solo_se_compara_el_monto_transferido():
    """Decisión del usuario (2026-10-09): ni número, ni banco, ni beneficiario."""
    obs = vehicular.revisar(_fuentes(), BORRADOR.replace("N° 00000001", "N° 00000007"))
    assert obs == []


def test_el_precio_debe_estar_en_el_acta():
    """Decisión del usuario (2026-10-09), también si se paga por transferencia."""
    sin_precio = BORRADOR.replace(
        "EL PRECIO ES DE S/ 12,345.00 (DOCE MIL TRESCIENTOS CUARENTA Y CINCO Y 00/100 SOLES)",
        "EL PRECIO ES EL PACTADO",
    )
    assert vehicular.revisar({"boleta-ficticia.pdf": BOLETA}, sin_precio) == [
        "[PRECIO] FALTA: «Precio de la transferencia» no aparece en el acta"
    ]


def test_sin_cheques_no_se_exige_monto():
    fuentes = {"boleta-ficticia.pdf": BOLETA}
    assert vehicular.revisar(fuentes, BORRADOR) == []


# F45: formato de tabla del acta («MARCA:  X  MODELO:  Y») y otros casos reales.
ACTA_TABLA = (
    "ACTA DE TRANSFERENCIA DE VEHICULO AUTOMOTOR POR COMPRA-VENTA\n"
    "CELEBRADA ENTRE: EMPRESA FICTICIA DEMO S.A.C., COMO LA TRANSFERENTE.\n"
    "PLACA N°:    QWE123  PARTIDA REGISTRAL N°   70000001\n"
    "MARCA:    MARCAFICTA  MODELO:   MODELOX\n"
    "SERIE:   9ZZZZ00ZZZ0000001  MOTOR:    MOT0000001\n"
    "PRECIO DE VENTA: US$ 1,000.00 (MIL Y 00/100 DOLARES AMERICANOS). =\n"
)


def test_formato_de_tabla_sin_errores():
    assert vehicular.revisar({"boleta-ficticia.pdf": BOLETA}, ACTA_TABLA) == []


def test_formato_de_tabla_detecta_el_modelo():
    acta = ACTA_TABLA.replace("MODELO:   MODELOX", "MODELO:   MODEX")
    assert vehicular.revisar({"boleta-ficticia.pdf": BOLETA}, acta) == [
        "[VEHICULO] «MODEX» debe decir «MODELOX»"
    ]


def test_formato_de_tabla_detecta_serie_y_motor():
    acta = ACTA_TABLA.replace("9ZZZZ00ZZZ0000001", "9ZZZZ00ZZZ0000002").replace(
        "MOT0000001", "MOT0000009"
    )
    assert vehicular.revisar({"boleta-ficticia.pdf": BOLETA}, acta) == [
        "[VEHICULO] «9ZZZZ00ZZZ0000002» debe decir «9ZZZZ00ZZZ0000001»",
        "[VEHICULO] «MOT0000009» debe decir «MOT0000001»",
    ]


def test_el_vehiculo_entregado_a_cuenta_no_se_compara():
    """Las características que siguen al precio son de otro vehículo."""
    acta = ACTA_TABLA + (
        "PRECIO DE VENTA: EL PAGO SE HA EFECTUADO A CUENTA DE OTRO VEHICULO "
        "DE MARCA: OTRAMARCA, MODELO: OTROMODELO, DEL AÑO MODELO 2030.\n"
    )
    assert vehicular.revisar({"boleta-ficticia.pdf": BOLETA}, acta) == []


def test_partida_corta_debe_decir():
    acta = ACTA_TABLA.replace("N°   70000001", "N°   7000")
    assert vehicular.revisar({"boleta-ficticia.pdf": BOLETA}, acta) == [
        "[PARTIDA] «7000» debe decir «70000001»"
    ]


BOLETA_PERSONA = BOLETA.replace("EMPRESA FICTICIA DEMO S.A.C.", "ZURBELIA LUMARIA ALBA")


def test_propietario_persona_natural_en_otro_orden():
    """La boleta lista apellidos y luego nombres; el acta, nombres primero."""
    acta = ACTA_TABLA.replace("EMPRESA FICTICIA DEMO S.A.C.", "ALBA ZURBELIA LUMARIA")
    assert vehicular.revisar({"boleta-ficticia.pdf": BOLETA_PERSONA}, acta) == []


def test_propietario_persona_mal_escrito_lo_observa_la_regla_de_nombres():
    """Con el orden cambiado no hay una corrección literal: la da NOMBRE (RENIEC)."""
    acta = ACTA_TABLA.replace("EMPRESA FICTICIA DEMO S.A.C.", "ALBA ZURBELIA LUMARI")
    assert vehicular.revisar({"boleta-ficticia.pdf": BOLETA_PERSONA}, acta) == []


def test_propietario_ausente():
    acta = ACTA_TABLA.replace("EMPRESA FICTICIA DEMO S.A.C.", "OTRA PERSONA DISTINTA")
    assert vehicular.revisar({"boleta-ficticia.pdf": BOLETA_PERSONA}, acta) == [
        "[PROPIETARIO] FALTA: «ZURBELIA LUMARIA ALBA» esta en las fuentes "
        "y no aparece en el destino"
    ]


# F45: constancia de depósito (abono) leída por OCR; decisión del usuario
# (2026-10-09): su monto debe coincidir con el acta, como el de un cheque.
ABONO = (
    "BCP\n"
    "SERVICIO DE RECAUDACION\n"
    "Empresa afiliada  EMPRESA FICTICIA DEMO S.A.C.\n"
    "Cuenta a Abonar\n"
    "CLIENTES SOLES\n"
    "Inporte  S/*****12,345.00\n"
    "Comisión  S/**********.00\n"
)


def test_monto_del_abono_presente():
    fuentes = {"boleta-ficticia.pdf": BOLETA, "abono-ficticio.jpeg": ABONO}
    assert vehicular.revisar(fuentes, BORRADOR) == []


def test_monto_del_abono_ausente():
    fuentes = {"boleta-ficticia.pdf": BOLETA, "abono-ficticio.jpeg": ABONO}
    assert vehicular.revisar(fuentes, BORRADOR.replace("12,345.00", "12,354.00")) == [
        "[CHEQUE] FALTA: «S/ 12,345.00» esta en las fuentes y no aparece en el destino"
    ]
