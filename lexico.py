"""Detector de erratas por vocabulario, determinista.

La idea: las escrituras YA FIRMADAS por la notaria son el diccionario. Una
palabra que nunca aparecio en ninguna escritura firmada, y que se parece mucho
a una que si, es una errata (OCTAO por OCTAVO). Una palabra rara que ya salio
en escrituras firmadas es vocabulario de la casa, no un error.

Esto cubre el vocabulario CERRADO (ordinales, formulas notariales) sin modelo y
sin varianza. Lo abierto —concordancia, sintaxis— sigue siendo del LLM.

  python3 lexico.py Resultado/ -d "Proyecto(borrador)/...docx"
"""

__all__ = ["contar", "erratas", "vocabulario", "main"]

import argparse
import sys
from pathlib import Path

from adaptadores.extraccion import DOCS, leer
from nucleo.lexico import contar, erratas


def vocabulario(rutas: list[str]):
    textos = []
    for ruta in rutas:
        p = Path(ruta)
        archivos = (
            sorted(x for x in p.rglob("*") if x.suffix.lower() in DOCS)
            if p.is_dir()
            else [p]
        )
        textos.extend(leer(archivo) for archivo in archivos)
    return contar(textos)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "firmadas", nargs="+", help="escrituras ya firmadas (el diccionario)"
    )
    ap.add_argument("-d", "--destino", required=True, help="borrador a revisar")
    ap.add_argument("-u", "--umbral", type=int, default=82)
    a = ap.parse_args()
    vocab = vocabulario(a.firmadas)
    print(
        f"corpus: {sum(vocab.values())} palabras, {len(vocab)} distintas",
        file=sys.stderr,
    )
    texto = leer(Path(a.destino))
    fuera = erratas(texto, vocab, a.umbral)
    for palabra, cerca, score in fuera:
        print(
            f"  «{palabra}» no aparece en ninguna escritura firmada   ¿querias decir «{cerca}»? ({score:.0f}%)"
        )
    print(f"\n{len(fuera)} palabras sospechosas")
    return 1 if fuera else 0


if __name__ == "__main__":
    sys.exit(main())
