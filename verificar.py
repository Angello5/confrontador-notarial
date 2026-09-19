"""Verifica un documento notarial contra sus archivos fuente (minuta + documentos).

  python3 verificar.py tests/fixtures/cliente/ -d tests/fixtures/borrador/observado.docx

Construye un CATALOGO de datos validos desde las fuentes, luego revisa CADA
aparicion en el destino. Un dato repetido dos veces se valida dos veces.
"""

__all__ = [
    "catalogo",
    "correspondencia",
    "diagnostico",
    "nombre_reniec",
    "nombres",
    "norm",
    "parrafos",
    "revisar",
    "revisar_parrafos",
    "main",
]

import argparse
import sys
from pathlib import Path

from adaptadores.extraccion import IMGS, recolectar
from nucleo.verificar import (
    catalogo,
    correspondencia,
    diagnostico,
    nombre_reniec,
    nombres,
    norm,
    parrafos,
    revisar,
    revisar_parrafos,
)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("fuentes", nargs="+", help="archivos o carpetas con la verdad")
    ap.add_argument(
        "-d", "--destino", nargs="+", required=True, help="documento(s) a revisar"
    )
    ap.add_argument(
        "-u", "--umbral", type=int, default=88, help="%% minimo de similitud de parrafo"
    )
    a = ap.parse_args()
    print("FUENTES:", file=sys.stderr)
    fuentes = recolectar(a.fuentes)
    print("DESTINO:", file=sys.stderr)
    destinos = recolectar(a.destino)
    cat = catalogo(fuentes)
    print("\nCatalogo de la fuente:", file=sys.stderr)
    for k, v in cat.items():
        print(f"  {k}: {', '.join(sorted(v)) or '(vacio)'}", file=sys.stderr)
    minutas = [v for k, v in fuentes.items() if Path(k).suffix.lower() not in IMGS]
    total = 0
    for nombre, txt in destinos.items():
        if aviso := diagnostico(fuentes, txt):
            print(f"\n=== {nombre} ===\n  !! {aviso}")
            print("  (no se compara campo por campo: seria ruido)")
            continue
        obs = revisar(cat, txt, a.umbral) + revisar_parrafos(minutas, txt, a.umbral)
        total += len(obs)
        print(f"\n=== {nombre} — {len(obs)} observacion(es) ===")
        for o in obs:
            print(" -", o)
        if not obs:
            print("  sin observaciones")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
