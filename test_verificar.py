"""Check minimo: el borrador malo debe salir observado y el resultado limpio.

Datos ficticios generados por scripts/generar_fixtures.py.

python -m pytest test_verificar.py
"""

from pathlib import Path
from itertools import product
import re
from time import perf_counter

import pytest

from adaptadores.extraccion import leer, recolectar
from nucleo.verificar import (
    RE_DNI_DOC,
    RE_NOMBRE,
    catalogo,
    correspondencia,
    diagnostico,
    nombres,
    revisar,
)

BASE = Path(__file__).parent / "tests" / "fixtures"


def test_re_dni_doc_rechaza_entrada_patologica_en_tiempo_lineal():
    inicio = perf_counter()
    assert RE_DNI_DOC.search("DNI" + " " * 5000 + "X") is None
    assert perf_counter() - inicio < 0.5


def test_re_nombre_rechaza_entrada_patologica_en_tiempo_lineal():
    inicio = perf_counter()
    assert RE_NOMBRE.search("ABCDEFGHIJ" + " " * 5000 + "X") is None
    assert perf_counter() - inicio < 0.5


RE_DNI_DOC_ORIGINAL = re.compile(
    r"(?:DNI|IDENTIDAD)\s*(?:N[O°]?|NUMERO)?\s*[:.]?\s*(\d{6,9})"
)


@pytest.mark.parametrize(
    "texto",
    [
        "DNI 90000001",
        "DNI: 90000001",
        "IDENTIDAD N° 90000001",
        "IDENTIDAD NUMERO: 90000001",
        "IDENTIDAD90000001",
        "CONDNI 90000004",
        "XDNI90000004",
        "CIUDAD NI 12345678",
        "D N I 12345678",
    ],
)
def test_re_dni_doc_equivale_a_la_original_salvo_d_n_i(texto):
    original = RE_DNI_DOC_ORIGINAL.search(texto)
    actual = RE_DNI_DOC.search(texto)
    assert (actual.group(1) if actual else None) == (
        original.group(1) if original else None
    )


@pytest.mark.parametrize(
    "texto",
    ["D.N.I. 90000001", "D.N.I 90000001"],
)
def test_re_dni_doc_acepta_d_n_i_decidido(texto):
    assert RE_DNI_DOC.search(texto).group(1) == "90000001"


@pytest.mark.parametrize("texto", ["CIUDAD NI 12345678", "D N I 12345678"])
def test_re_dni_doc_no_acepta_letras_separadas_ni_falso_positivo(texto):
    assert RE_DNI_DOC.search(texto) is None


RE_NOMBRE_ORIGINAL = re.compile(
    r"([A-Z][A-Z ]{8,60}?)\s*[,.]{0,2}-?\s*(?:DE\s+)?NACIONALIDAD"
    r"|CASAD[AO]\s+CON\s+([A-Z][A-Z ]{8,60}?)\s*[,.]"
)


def _nombres_con(regex, texto):
    out = []
    for a, b in regex.findall(texto):
        palabras = [x for x in (a or b).split() if x not in {"DE", "PERUANA"}]
        if 2 <= len(palabras) <= 5:
            out.append(" ".join(palabras))
    return out


_NOMBRES_CORPUS = tuple(
    " ".join(partes) + sufijo
    for partes, sufijo in product(
        [
            ("ANA", "LUZ", "QUISPE", "MAMANI"),
            ("BRUNO", "SOL", "PAREDES", "ROJAS"),
            ("CIRA", "MAR", "SALAS", "TORRES"),
        ],
        [" DE NACIONALIDAD PERUANA", ", DE NACIONALIDAD PERUANA", " NACIONALIDAD"],
    )
)


@pytest.mark.parametrize("texto", _NOMBRES_CORPUS)
def test_re_nombre_equivale_a_la_original(texto):
    assert nombres(texto) == _nombres_con(RE_NOMBRE_ORIGINAL, texto)


def test_re_nombre_conserva_nombre_sin_coma():
    assert nombres("ANA LUZ QUISPE MAMANI DE NACIONALIDAD PERUANA") == [
        "ANA LUZ QUISPE MAMANI"
    ]


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        (
            "LUCAS DE LA VEGA ZAFIRO, DE NACIONALIDAD PERUANA.",
            ["LUCAS DE LA VEGA ZAFIRO"],
        ),
        (
            "ELENA DE LOS ASTROS DE LA TORRE, DE NACIONALIDAD PERUANA.",
            ["ELENA DE LOS ASTROS DE LA TORRE"],
        ),
        (
            "MATEO Y DEL BOSQUE RIOS, DE NACIONALIDAD PERUANA.",
            ["MATEO Y DEL BOSQUE RIOS"],
        ),
    ],
)
def test_nombres_conserva_particulas_internas(texto, esperado):
    assert RE_NOMBRE.search(texto)
    assert nombres(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "DE LUCAS LUZ ZAFIRO, DE NACIONALIDAD PERUANA.",
        "LUCAS LUZ ZAFIRO LA, DE NACIONALIDAD PERUANA.",
    ],
)
def test_nombres_descarta_particula_suelta_en_extremo(texto):
    assert RE_NOMBRE.search(texto)
    assert nombres(texto) == ["LUCAS LUZ ZAFIRO"]


def test_revisar_no_observa_nombre_compuesto_igual_en_fuente_y_borrador():
    texto = "LUCAS DE LA VEGA ZAFIRO, DE NACIONALIDAD PERUANA."
    cat = catalogo({"cliente.txt": texto})

    assert cat["NOMBRE"] == {"LUCAS DE LA VEGA ZAFIRO"}
    assert correspondencia(cat, texto) == (1.0, 0)
    assert revisar(cat, texto, 88) == []


def test_revisar_reporta_nombre_compuesto_alterado_completo():
    fuente = "LUCAS DE LA VEGA ZAFIRO, DE NACIONALIDAD PERUANA."
    borrador = "LUCAS DE LA VEGA ZAFIRA, DE NACIONALIDAD PERUANA."
    cat = catalogo({"cliente.txt": fuente})

    observaciones = revisar(cat, borrador, 88)

    assert any(
        "[NOMBRE] «LUCAS DE LA VEGA ZAFIRA» debe decir «LUCAS DE LA VEGA ZAFIRO»"
        in observacion
        for observacion in observaciones
    )


def test_revisar_no_duplica_nombre_compuesto_repetido_en_caratula():
    fuente = "LUCAS DE LA VEGA ZAFIRO, DE NACIONALIDAD PERUANA."
    borrador = "LUCAS DE LA VEGA ZAFIRA\nLUCAS DE LA VEGA ZAFIRA"
    cat = catalogo({"cliente.txt": fuente})

    observaciones = revisar(cat, borrador, 88)

    assert observaciones == [
        "[NOMBRE] «LUCAS DE LA VEGA ZAFIRA» debe decir «LUCAS DE LA VEGA ZAFIRO»   (caratula)"
    ]


def test_correspondencia_y_diagnostico_sinteticos():
    fuentes = {"cliente.txt": "NOMBRE ANA LUZ QUISPE MAMANI DNI 90000001"}
    cat = catalogo(fuentes)
    assert correspondencia(cat, "ANA LUZ QUISPE MAMANI DNI 90000001") == (1.0, 0)
    assert correspondencia(cat, "OTRA PERSONA DNI 90000002 DNI 90000003") == (0.0, 2)
    assert diagnostico(fuentes, "ANA LUZ QUISPE MAMANI DNI 90000001") is None
    assert "no corresponde" in (
        diagnostico(fuentes, "OTRA PERSONA DNI 90000002 DNI 90000003") or ""
    )


def test_verificacion(monkeypatch, tmp_path):
    from adaptadores import extraccion

    monkeypatch.setattr(extraccion, "CACHE", tmp_path / "cache")
    fuentes = recolectar([str(BASE / "cliente")])
    cat = catalogo(fuentes)
    assert cat["DNI"] == {"90000001", "90000002", "90000003", "90000004"}, cat["DNI"]
    assert cat["PARTIDA"] == {"80000001"}, cat["PARTIDA"]
    assert len(cat["NOMBRE"]) == 4, cat["NOMBRE"]  # sin basura del sello de agua

    def obs(p):
        return revisar(cat, next(iter(recolectar([str(p)]).values())), 88)

    malo = obs(BASE / "borrador" / "observado.docx")
    bueno = obs(BASE / "resultado" / "correcto.docx")
    assert len(malo) >= 6, malo
    assert bueno == [], bueno  # sin falsos positivos
    # el borrador correcto SI corresponde a sus fuentes; una plantilla ajena no
    from nucleo.verificar import diagnostico

    borrador = next(iter(recolectar([str(BASE / "borrador")]).values()))
    assert diagnostico(fuentes, borrador) is None, diagnostico(fuentes, borrador)
    ajeno = leer(BASE / "ajeno" / "plantilla.docx")
    assert "no corresponde" in (diagnostico(fuentes, ajeno) or ""), diagnostico(
        fuentes, ajeno
    )
    # una plantilla ajena MEZCLADA entre las fuentes no debe hundir a la minuta
    assert diagnostico(fuentes | {"plantilla.docx": ajeno}, borrador) is None

    print(
        f"OK — borrador: {len(malo)} observaciones, resultado: 0, plantilla ajena bloqueada"
    )


def test_catalogo_clasifica_imagenes_por_suffix_path_y_compartida_imags():
    def reniec(nombre):
        return (
            f"NOMBRES  {nombre}\nAPELLIDO PATERNO  ZURBELIA\nAPELLIDO MATERNO  LUMARIA"
        )

    cat = catalogo(
        {
            "foto.PNG": reniec("ALBA"),
            "foto.png": reniec("BRISA"),
            ".png": reniec("CARLA"),
        }
    )
    assert cat["NOMBRE"] == {"ALBA ZURBELIA LUMARIA", "BRISA ZURBELIA LUMARIA"}
