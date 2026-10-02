"""Reglas F30 con textos inventados y sin adaptadores ni documentos reales."""

from nucleo.correccion import correcciones
from nucleo.verificar import catalogo, datos_registrales, revisar


def _observaciones(fuente: str, borrador: str, campo: str) -> list[str]:
    salidas = revisar(catalogo({"minuta-ficticia.txt": fuente}), borrador, 90)
    return [salida for salida in salidas if salida.startswith(f"[{campo}]")]


def test_area_en_letras_y_cifra_en_ambos_ordenes():
    fuente = "EL INMUEBLE FICTICIO TIENE UN AREA DE 100 M2."
    assert _observaciones(fuente, "CIEN METROS CUADRADOS (101 M2)", "AREA") == [
        "[AREA] «CIEN METROS CUADRADOS (101 M2)» debe decir «101 M2»"
    ]
    assert _observaciones(fuente, "101 M2 (CIEN METROS CUADRADOS)", "AREA") == [
        "[AREA] «101 M2 (CIEN METROS CUADRADOS)» debe decir «101 M2»"
    ]
    assert _observaciones(fuente, "CIEN METROS CUADRADOS (100 M2)", "AREA") == []
    assert (
        _observaciones(
            fuente,
            "CIEN METROS CUADRADOS CON CINCUENTA DECIMETROS CUADRADOS (100.50 M2)",
            "AREA",
        )
        == []
    )
    assert (
        _observaciones(
            fuente,
            "100.50 M2 (CIEN METROS CUADRADOS CON CINCUENTA DECIMETROS CUADRADOS)",
            "AREA",
        )
        == []
    )


def test_numero_en_letras_con_moneda_decimales_y_porcentaje():
    fuente = "CUOTA S/ 101.00."
    assert (
        len(_observaciones(fuente, "CIEN SOLES (S/ 101.00)", "NUMERO_EN_LETRAS")) == 1
    )
    assert (
        len(
            _observaciones(
                fuente, "S/ 101.00 (CIEN Y 00/100 SOLES)", "NUMERO_EN_LETRAS"
            )
        )
        == 1
    )
    assert (
        len(_observaciones(fuente, "CINCUENTA POR CIENTO (51%)", "NUMERO_EN_LETRAS"))
        == 1
    )
    assert _observaciones(fuente, "CIEN SOLES (S/ 100.00)", "NUMERO_EN_LETRAS") == []


def test_correlativos_de_clausulas_e_incisos_reiniciados():
    borrador = (
        "CLAUSULA PRIMERA: OBJETO\n"
        "A) PRIMER INCISO\n"
        "C) TERCER INCISO\n"
        "CLAUSULA TERCERA: PRECIO\n"
        "A) INCISO DE LA SIGUIENTE CLAUSULA\n"
    )
    assert _observaciones("MINUTA FICTICIA", borrador, "CORRELATIVO") == [
        "[CORRELATIVO] «C)» debe decir «B)»   (cláusula PRIMERA)",
        "[CORRELATIVO] «CLAUSULA TERCERA:» debe decir «CLAUSULA SEGUNDA:»",
    ]


def test_copropiedad_omite_totales_validos_y_evitar_doble_conteo():
    fuente = "COPROPIEDAD DEL INMUEBLE FICTICIO."
    assert (
        len(
            _observaciones(
                fuente, "LA COPROPIEDAD ES 40% DE ANA Y 50% DE EVA.", "COPROPIEDAD"
            )
        )
        == 1
    )
    for texto in (
        "LA COPROPIEDAD ES 40% DE ANA Y 60% DE EVA.",
        "LA COPROPIEDAD ES 50% (CINCUENTA POR CIENTO) DE ANA Y 50% DE EVA.",
        "LA COPROPIEDAD ES 33.33% DE ANA, 33.33% DE EVA Y 33.33% DE LUZ.",
        "CADA UNO TIENE 40% DE LA COPROPIEDAD Y ADQUIERE 50% DEL BIEN.",
    ):
        assert _observaciones(fuente, texto, "COPROPIEDAD") == [], texto


def test_precio_sin_moneda_se_compara_por_concepto():
    fuente = "PRECIO 250,000.00. TASACION 25,000.00."
    assert _observaciones(fuente, "PRECIO 25,000.00. TASACION 25,000.00.", "MONTO") == [
        "[MONTO] «25,000.00» debe decir «250,000.00»   (concepto: PRECIO)"
    ]
    assert _observaciones(fuente, fuente, "MONTO") == []


def test_registro_y_zona_con_fuente_y_sede_conocida():
    fuente = (
        "ZONA REGISTRAL N° IX SEDE LIMA. REGISTRO DE PREDIOS. "
        "OFICINA REGISTRAL DE LIMA. PROVINCIA DE LIMA."
    )
    borrador = (
        "ZONA REGISTRAL N° VIII SEDE LIMA. REGISTRO DE PERSONAS JURIDICAS. "
        "OFICINA REGISTRAL DE LIMA. PROVINCIA DE LIMA."
    )
    observaciones = _observaciones(fuente, borrador, "DATO_REGISTRAL")
    assert any("ZONA REGISTRAL N° VIII" in obs and "IX" in obs for obs in observaciones)
    assert any("SEDE LIMA" in obs and "HUANCAYO" in obs for obs in observaciones)
    assert any(
        "REGISTRO DE PERSONAS JURIDICAS" in obs and "PREDIOS" in obs
        for obs in observaciones
    )
    assert len(observaciones) == 3
    assert _observaciones(fuente, fuente, "DATO_REGISTRAL") == []


def test_provincia_con_articulo_inicial_se_extrae_y_compara():
    fuente = "EL BIEN FICTICIO SE UBICA EN LA PROVINCIA DE LA CONVENCION."
    borrador = "EL BIEN FICTICIO SE UBICA EN LA PROVINCIA DE LA CONVENCIO."
    assert [(clase, valor) for clase, valor, _ in datos_registrales(fuente)] == [
        ("PROVINCIA", "LA CONVENCION")
    ]
    assert _observaciones(fuente, borrador, "DATO_REGISTRAL") == [
        "[DATO_REGISTRAL] «PROVINCIA DE LA CONVENCIO» debe decir «PROVINCIA DE LA CONVENCION»"
    ]


def test_regla_sin_texto_correcto_no_entra_en_correccion_automatica():
    salidas = [
        "[AREA] «CIEN METROS CUADRADOS (101 M2)» debe decir «101 M2»",
        "[CORRELATIVO] «CLAUSULA TERCERA:» debe decir «CLAUSULA SEGUNDA:»",
        "[COPROPIEDAD] «40% Y 50%» debe decir «100 %»",
        "[DATO_REGISTRAL] «REGISTRO DE PREDIOS» debe decir «REGISTRO DE SOCIEDADES»",
    ]
    fuentes = {"ficticia.txt": "REGISTRO DE SOCIEDADES. AREA 101 M2."}
    assert [(c["campo"], c["correcto"]) for c in correcciones(salidas, fuentes)] == [
        ("DATO_REGISTRAL", "REGISTRO DE SOCIEDADES")
    ]
