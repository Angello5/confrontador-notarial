"""Compatibilidad temporal de CLI; las reglas viven en `nucleo.lexico`."""

import argparse
import sys

from adaptadores.extraccion import recolectar

__all__ = ["contar", "erratas", "vocabulario", "main"]

from nucleo.lexico import contar, erratas


def vocabulario(rutas: list[str]):
    return contar(recolectar(rutas).values())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
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
    texto = next(iter(recolectar([a.destino]).values()))
    fuera = erratas(texto, vocab, a.umbral)
    for palabra, cerca, score in fuera:
        print(
            f"  «{palabra}» no aparece en ninguna escritura firmada   ¿querias decir «{cerca}»? ({score:.0f}%)"
        )
    print(f"\n{len(fuera)} palabras sospechosas")
    return 1 if fuera else 0


if __name__ == "__main__":
    sys.exit(main())
