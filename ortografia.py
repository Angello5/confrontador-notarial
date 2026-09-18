"""Compatibilidad temporal; reglas en `nucleo.ortografia`, recursos en adaptadores."""

__all__ = [
    "DIC",
    "LISTA",
    "URL",
    "agregar_a_lista",
    "diccionario",
    "lista_casa",
    "plano",
    "revisar",
    "tildada",
    "main",
]

from adaptadores.diccionario import (
    DIC,
    LISTA,
    URL,
    agregar_a_lista,
    diccionario,
    lista_casa,
)
from nucleo.ortografia import plano, revisar as _revisar, tildada


def revisar(texto: str, extra=frozenset()):
    d, lemas = diccionario()
    return _revisar(texto, d, lemas, lista_casa(), extra)


def main():
    """Revisa la ortografía de un documento local.

    Uso: ``python ortografia.py documento.docx``.
    """
    import argparse
    from adaptadores.extraccion import leer
    from pathlib import Path

    ap = argparse.ArgumentParser(
        description=main.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("documento")
    a = ap.parse_args()
    hallazgos = revisar(leer(Path(a.documento)))
    for w, motivo, sugerencia in hallazgos:
        print(f"  «{w}» {motivo}   ¿{sugerencia}?")
    print(
        f"\n{len(hallazgos)} palabras marcadas · lista de la casa: {len(lista_casa())} terminos"
    )
    return 1 if hallazgos else 0


if __name__ == "__main__":
    raise SystemExit(main())
