"""Corrector ortografico determinista para texto notarial peruano.

Usa hunspell (es_PE de LibreOffice) via spylls, en Python puro. El diccionario
se carga en el adaptador y se inyecta junto con la lista de la casa.

Dos decisiones que hacen que funcione sobre escrituras:

1. Las MAYUSCULAS SIN TILDE se aceptan. La notaria escribe OBLIGACION y
   OBLIGACIÓN en el mismo documento; no hay regla que hacer cumplir. Pero una
   tilde MAL PUESTA (CLAÚSULA) si es un error, y ahi la palabra ya trae tilde.

2. Las sugerencias NO las da hunspell. Su busqueda tarda hasta 11 s en una sola
   palabra larga y deformada. Para la tilde mal puesta la correccion es exacta
   y para el resto va rapidfuzz.
"""

import re
import unicodedata

from rapidfuzz import fuzz, process

VOCALES = "aeiou"

AGUDA = dict(zip(VOCALES, "áéíóú"))


def plano(t: str) -> str:
    d = unicodedata.normalize("NFKD", t)
    return "".join(c for c in d if not unicodedata.combining(c)).lower()


def tildada(w: str) -> bool:
    return any(unicodedata.combining(c) for c in unicodedata.normalize("NFKD", w))


def revisar(
    texto: str, d, lemas: list[str], lista: set[str], extra: set[str] = frozenset()
) -> list[tuple[str, str, str]]:
    """[(palabra, motivo, sugerencia)] de lo que no es castellano valido.

    `extra` son palabras a dar por buenas ademas de la lista: los nombres de las
    partes, que ya valida la capa de reglas contra el DNI y la minuta.
    """
    aceptadas = lista | {e.upper() for e in extra}
    fuera = []
    for w in dict.fromkeys(re.findall(r"[^\W\d_]{3,}", texto)):
        # se consulta TAL CUAL antes que en minuscula: hunspell acepta el nombre
        # propio solo capitalizado (Peru falla, Perú y PERÚ pasan) y el documento
        # notarial ya viene en mayusculas
        if w.upper() in aceptadas or d.lookup(w) or d.lookup(w.lower()):
            continue
        base = plano(w)
        if not tildada(w):
            # sin tilde: si alguna forma tildada existe, es la convencion de mayusculas
            if any(
                d.lookup(v) or d.lookup(v.upper())
                for i, c in enumerate(base)
                if c in VOCALES
                for v in [base[:i] + AGUDA[c] + base[i + 1 :]]
            ):
                continue
        elif d.lookup(base) or d.lookup(base.upper()):
            fuera.append((w, "tilde mal puesta", base))  # correccion exacta
            continue
        m = process.extractOne(base, lemas, scorer=fuzz.ratio)
        fuera.append((w, "no existe en castellano", m[0] if m and m[1] >= 75 else "?"))
    return fuera
