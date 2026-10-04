"""F27: montos por posición, con moneda y concepto (datos ficticios)."""

from nucleo.verificar import SEPARADOR_PAGINA, catalogo, montos_exigibles, revisar

_CRONOGRAMA = (
    "CRONOGRAMA DE PAGOS\n"
    "CUOTA 1 15/01/2027 S/ 1,000.00 S/ 50.00 S/ 1,050.00\n"
    "CUOTA 2 15/02/2027 S/ 1,000.00 S/ 45.00 S/ 1,045.00\n"
    "CUOTA 3 15/03/2027 S/ 1,000.00 S/ 40.00 S/ 1,040.00\n"
)
_PRECIO = (
    "CLAUSULA SEGUNDA. PRECIO DE VENTA: S/ 250,000.00, QUE EL COMPRADOR PAGA "
    "CON ARRAS DE S/ 25,000.00 Y EL SALDO AL CONTADO EN LA FECHA DE FIRMA."
)
_MINUTA = "MINUTA FICTICIA" + SEPARADOR_PAGINA + _PRECIO + "\n" + _CRONOGRAMA


def _montos(borrador, minuta=_MINUTA, con_minuta=True):
    fuentes = {"minuta-ficticia.txt": minuta}
    return [
        o
        for o in revisar(
            catalogo(fuentes),
            borrador,
            88,
            None,
            montos_exigibles([minuta]),
            fuentes if con_minuta else None,
        )
        if o.startswith("[MONTO] «")
    ]


def test_monedas_antes_y_despues_de_la_cifra():
    texto = (
        "A S/. 1.00 B 2.00 SOLES C 3.00 DOLARES AMERICANOS D $ 4.00 E US$5.00 "
        "F DOLARES 6.00 G S/ 7.00"
    )
    assert catalogo({"m.txt": texto})["MONTO"] == {
        "1.00",
        "2.00",
        "US$ 3.00",
        "US$ 4.00",
        "US$ 5.00",
        "US$ 6.00",
        "7.00",
    }


def test_soles_y_dolares_del_mismo_importe_son_distintos():
    assert _montos("PRECIO S/ 100.00.", "PRECIO US$ 100.00.") == [
        "[MONTO] «100.00» debe decir «US$ 100.00»"
    ]


def test_importe_en_dolares_alterado():
    assert _montos("PRECIO US$ 80,500.00.", "PRECIO US$ 80,000.00.") == [
        "[MONTO] «US$ 80,500.00» debe decir «US$ 80,000.00»"
    ]


def test_cuota_con_el_importe_de_otra_cuota():
    borrador = _PRECIO + "\n" + _CRONOGRAMA.replace("S/ 1,045.00", "S/ 1,040.00")
    assert _montos(borrador) == [
        "[MONTO] «1,040.00» debe decir «1,045.00»   "
        "(concepto: CUOTA 2; fuente: minuta-ficticia.txt, p. 2)"
    ]


def test_fila_por_fecha_sin_numero_de_cuota():
    minuta = "15/01/2027 S/ 500.00 S/ 20.00\n15/02/2027 S/ 500.00 S/ 10.00\n"
    borrador = "15/02/2027 S/ 500.00 S/ 20.00\n15/01/2027 S/ 500.00 S/ 20.00\n"
    assert _montos(borrador, minuta) == [
        "[MONTO] «20.00» debe decir «10.00»   "
        "(concepto: CUOTA DEL 15/02/2027; fuente: minuta-ficticia.txt, p. 1)"
    ]


def test_precio_sustituido_por_otro_importe_valido():
    borrador = _PRECIO.replace("S/ 250,000.00", "S/ 25,000.00") + "\n" + _CRONOGRAMA
    assert _montos(borrador) == [
        "[MONTO] «25,000.00» debe decir «250,000.00»   "
        "(concepto: CLAUSULA SEGUNDA PRECIO DE VENTA; "
        "fuente: minuta-ficticia.txt, p. 2)"
    ]


def test_cronograma_identico_sin_observaciones():
    assert _montos(_PRECIO + "\n" + _CRONOGRAMA) == []


def test_parrafo_sin_par_conserva_la_regla_actual():
    borrador = (
        _PRECIO
        + "\n"
        + _CRONOGRAMA
        + "LOS GASTOS NOTARIALES Y REGISTRALES DE ESTA ESCRITURA SERAN ASUMIDOS "
        "POR AMBAS PARTES HASTA UN TOPE DE S/ 99.99 CADA UNA."
    )
    assert _montos(borrador) == ["[MONTO] «99.99» no coincide con ninguna fuente"]


def test_sin_minutas_la_verificacion_es_por_conjunto():
    borrador = _PRECIO.replace("S/ 250,000.00", "S/ 25,000.00") + "\n" + _CRONOGRAMA
    # F30: el conjunto acepta 25,000.00 (son las arras); el concepto PRECIO no.
    assert _montos(borrador, con_minuta=False) == [
        "[MONTO] «25,000.00» debe decir «250,000.00»   (concepto: PRECIO)"
    ]


def test_par_con_distinto_numero_de_importes_usa_la_regla_actual():
    borrador = _PRECIO.replace(" CON ARRAS DE S/ 25,000.00", "") + "\n" + _CRONOGRAMA
    assert _montos(borrador) == []


def test_importe_partido_entre_lineas_usa_la_regla_actual():
    assert _montos("PRECIO US$\n80,500.00.", "PRECIO US$ 80,000.00.") == [
        "[MONTO] «US$ 80,500.00» debe decir «US$ 80,000.00»"
    ]


def test_cifra_con_miles_mal_agrupados_no_es_un_monto():
    # Lectura OCR que se comió un cero: «47,000.00» leído «47,00.00».
    texto = (
        "A US$47,00.00 B S/138,00.00 C 1,00.00 SOLES D S/ 1,0000.00 "
        "E S/ 138,000.00 F US$ 900.00"
    )
    assert catalogo({"m.txt": texto})["MONTO"] == {"138,000.00", "US$ 900.00"}


def test_minuta_mal_leida_no_propone_su_cifra_al_borrador():
    minuta = _MINUTA.replace("S/ 250,000.00", "S/ 250,00.00")
    borrador = _PRECIO
    assert not [o for o in _montos(borrador, minuta) if "250,00.00" in o]


def test_lectura_mal_formada_conserva_su_posicion_en_el_parrafo():
    parrafo = (
        "EL GARANTE FICTICIO RECIBE EL CAPITAL EQUIVALENTE A US$ {} AL TIPO DE "
        "CAMBIO DEL DIA, Y ADEMAS LA SUMA DE S/ 19,000.00 MEDIANTE CHEQUE DE GERENCIA."
    )
    minuta = "MINUTA FICTICIA" + SEPARADOR_PAGINA + parrafo.format("47,00.00")
    assert _montos(parrafo.format("47,000.00"), minuta) == []


def test_monto_sin_par_que_la_minuta_lee_mal_no_sugiere_otro_importe():
    minuta = (
        "MINUTA FICTICIA" + SEPARADOR_PAGINA + "EL CAPITAL ES US$ 47,00.00.\n"
        "LA SUMA DE S/ 19,000.00 SE ENTREGA CON CHEQUE.\n"
    )
    borrador = "EL CAPITAL ES US$ 47,000.00 Y LA SUMA DE S/ 19,000.00 SE ENTREGA."
    assert _montos(borrador, minuta) == []


def test_monto_distinto_de_la_lectura_mal_formada_se_sigue_observando():
    minuta = "MINUTA FICTICIA" + SEPARADOR_PAGINA + "EL CAPITAL ES US$ 47,00.00.\n"
    borrador = "EL CAPITAL ES US$ 45,000.00."
    assert _montos(borrador, minuta) != []
