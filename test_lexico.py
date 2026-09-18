"""Test de lexico.py con documentos ficticios generados localmente.

python -m pytest test_lexico.py
"""

from pathlib import Path

from adaptadores.extraccion import leer
from lexico import vocabulario
from nucleo.lexico import contar, erratas

BASE = Path(__file__).parent / "tests" / "fixtures"
FIRMADA = BASE / "resultado" / "correcto.docx"
BORRADOR = BASE / "borrador" / "observado.docx"
MINUTA = BASE / "cliente" / "minuta.docx"


def test_lexico():
    vocab = vocabulario([str(FIRMADA)])

    hallado = {p: c for p, c, _ in erratas(leer(BORRADOR), vocab)}
    for mal, bien in [
        ("OCTAO", "OCTAVO"),
        ("DECIO", "DECIMO"),
        ("MEIO", "MEDIO"),
        ("UIRBANIZACION", "URBANIZACION"),
        ("OCUPACIÒN", "OCUPACIÓN"),
        ("TIENE", "TIENEN"),
    ]:
        assert hallado.get(mal) == bien, (
            f"{mal}: esperaba {bien}, dio {hallado.get(mal)}"
        )

    # la escritura firmada es el corpus: no puede acusarse a si misma
    assert erratas(leer(FIRMADA), vocab) == [], erratas(leer(FIRMADA), vocab)

    # sobre un documento legitimo distinto, solo debe marcar errores de verdad
    en_minuta = {p for p, _, _ in erratas(leer(MINUTA), vocab)}
    assert en_minuta == {"OCUPACIÒN", "UIRBANIZACION", "TIENE"}, en_minuta

    # el acento grave no necesita corpus: en castellano no existe
    solo_acento = erratas("LA OCUPACIÒN Y EL ARTÌCULO", contar([]))
    assert [c for _, c, _ in solo_acento] == ["OCUPACIÓN", "ARTÍCULO"], solo_acento

    # flexion: plural y genero no son erratas, pero una letra faltante si
    v2 = contar(["LA CLAUSULA SUSCRITA POR ZURBELIA Y LA IMPRESION DACTILAR"])
    marcadas = {
        p
        for p, _, _ in erratas(
            "LAS CLAUSULAS SUSCRITO IMPRESIONES DACTILARES DE ZURBELI", v2
        )
    }
    assert marcadas == {"ZURBELI"}, marcadas

    print(
        f"OK — {len(hallado)} erratas en el borrador, 0 en la firmada, "
        f"{len(en_minuta)} erratas en la minuta ficticia"
    )


def test_vocabulario_incluye_archivos_homonimos_en_subcarpetas(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "firmada.txt").write_text("CLAUSULA OCTAVO FERROVIARIO")
    (tmp_path / "b" / "firmada.txt").write_text("CLAUSULA NOVENO")

    hallazgos = erratas("FERROVIARIA FERROVIARIX", vocabulario([str(tmp_path)]))

    assert [(p, c, round(s, 1)) for p, c, s in hallazgos] == [
        ("FERROVIARIX", "FERROVIARIO", 90.9)
    ]
