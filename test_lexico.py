"""Check de lexico.py contra los documentos reales del caso.

  python3 test_lexico.py
"""
from pathlib import Path

from extraer import leer
from lexico import erratas, vocabulario

BASE = Path(__file__).parent
FIRMADA = BASE / "Resultado" / "72156.docx"
BORRADOR = BASE / "Proyecto(borrador)" / "1785794688639_71168_malo2.docx"
MINUTA = BASE / "Cliente" / "1785794688252_DONACION_ACCIONES_Y_DERECHOS_-_KARIN.docx"

if __name__ == "__main__":
    vocab = vocabulario([str(FIRMADA)])

    hallado = {p: c for p, c, _ in erratas(leer(BORRADOR), vocab)}
    for mal, bien in [("OCTAO", "OCTAVO"), ("DECIO", "DECIMO"), ("MEIO", "MEDIO"),
                      ("UIRBANIZACION", "URBANIZACION"), ("OCUPACIÒN", "OCUPACIÓN"),
                      ("TIENE", "TIENEN")]:
        assert hallado.get(mal) == bien, f"{mal}: esperaba {bien}, dio {hallado.get(mal)}"

    # la escritura firmada es el corpus: no puede acusarse a si misma
    assert erratas(leer(FIRMADA), vocab) == [], erratas(leer(FIRMADA), vocab)

    # sobre un documento legitimo distinto, solo debe marcar errores de verdad
    en_minuta = {p for p, _, _ in erratas(leer(MINUTA), vocab)}
    assert en_minuta == {"OCUPACIÒN", "UIRBANIZACION", "TIENE"}, en_minuta

    # el acento grave no necesita corpus: en castellano no existe
    solo_acento = erratas("LA OCUPACIÒN Y EL ARTÌCULO", vocabulario([]))
    assert [c for _, c, _ in solo_acento] == ["OCUPACIÓN", "ARTÍCULO"], solo_acento

    # flexion: plural y genero no son erratas, pero una letra faltante si
    from lexico import contar
    v2 = contar(["LA CLAUSULA SUSCRITA POR MENDOZA Y LA IMPRESION DACTILAR"])
    marcadas = {p for p, _, _ in erratas(
        "LAS CLAUSULAS SUSCRITO IMPRESIONES DACTILARES DE MENDOZ", v2)}
    assert marcadas == {"MENDOZ"}, marcadas

    print(f"OK — {len(hallado)} erratas en el borrador, 0 en la firmada, "
          f"{len(en_minuta)} reales en la minuta")
