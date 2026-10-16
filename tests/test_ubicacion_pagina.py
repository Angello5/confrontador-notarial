"""F32: ubicación de un valor observado sobre los segmentos de una página (ficticio)."""

import pytest

from nucleo.correccion import marcas


def seg(texto, x0, x1, linea, y0=0.1, alto=0.02):
    """Segmento con caracteres de igual ancho."""
    n = len(texto)
    bordes = tuple(x0 + (x1 - x0) * i / n for i in range(n + 1))
    return (texto, x0, y0 + linea * 0.05, x1, y0 + linea * 0.05 + alto, linea, bordes)


LINEA_0 = [
    seg("DNI", 0.10, 0.15, 0),
    seg("90000002,", 0.16, 0.26, 0),
    seg("ALBA", 0.27, 0.32, 0),
    seg("ZURBELIA", 0.33, 0.43, 0),
]


def test_valor_en_un_segmento():
    assert marcas(LINEA_0, "ALBA") == [
        {"x0": 0.27, "y0": 0.1, "x1": 0.32, "y1": 0.12, "aparicion": 0}
    ]


def test_valor_partido_en_dos_segmentos_de_la_misma_linea():
    resultado = marcas(LINEA_0, "ALBA ZURBELIA")
    assert [(r["x0"], r["x1"]) for r in resultado] == [(0.27, 0.32), (0.33, 0.43)]
    assert {r["aparicion"] for r in resultado} == {0}


def test_valor_que_cruza_dos_lineas():
    segmentos = [
        seg("COMPRADORA", 0.10, 0.30, 0),
        seg("ALBA", 0.80, 0.88, 0),
        seg("ZURBELIA", 0.10, 0.25, 1),
        seg("LUNARIA", 0.26, 0.40, 1),
    ]
    resultado = marcas(segmentos, "ALBA ZURBELIA LUNARIA")
    assert len(resultado) == 3
    assert {r["aparicion"] for r in resultado} == {0}
    assert resultado[0]["y0"] < resultado[1]["y0"]


def test_varias_apariciones_en_orden_de_lectura():
    segmentos = [seg("ALBA", 0.1, 0.2, 0), seg("ALBA", 0.5, 0.6, 2)]
    assert [r["aparicion"] for r in marcas(segmentos, "alba")] == [0, 1]


def test_valor_dentro_de_un_segmento_por_sus_caracteres():
    # «90000002,» tiene 9 caracteres de igual ancho; el valor ocupa los 8 primeros.
    (rect,) = marcas(LINEA_0, "90000002")
    assert rect["x0"] == pytest.approx(0.16)
    assert rect["x1"] == round(0.16 + 0.10 * 8 / 9, 4)


def test_tildes_y_mayusculas_como_el_nucleo():
    segmentos = [seg("Pérez", 0.1, 0.2, 0)]
    assert len(marcas(segmentos, "PEREZ")) == 1


def test_limite_de_palabra():
    assert marcas([seg("ALBARRACIN", 0.1, 0.3, 0)], "ALBA") == []


@pytest.mark.parametrize("valor", ["", "   ", "LUMARIA"])
def test_sin_marcas(valor):
    assert marcas(LINEA_0, valor) == []


def test_sin_segmentos():
    assert marcas([], "ALBA") == []


def test_determinista():
    assert marcas(LINEA_0, "ALBA ZURBELIA") == marcas(list(LINEA_0), "ALBA ZURBELIA")


def test_borde_del_ultimo_caracter_y_no_por_proporcion():
    # F52: en «LUNARIA,» la coma es más estrecha que las letras en negrita; por
    # proporción el recuadro dejaba fuera la última A.
    bordes = (0.30, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37, 0.373)
    segmento = ("LUNARIA,", 0.30, 0.1, 0.373, 0.12, 0, bordes)
    (rect,) = marcas([segmento], "LUNARIA")
    assert (rect["x0"], rect["x1"]) == (0.30, 0.37)
