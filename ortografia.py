"""Corrector ortografico determinista para texto notarial peruano.

Usa hunspell (es_PE de LibreOffice) via spylls, en Python puro. El diccionario
son 0.8 MB en disco y ~55 MB en RAM; se carga una vez y se queda residente.

Dos decisiones que hacen que funcione sobre escrituras:

1. Las MAYUSCULAS SIN TILDE se aceptan. La notaria escribe OBLIGACION y
   OBLIGACIÓN en el mismo documento; no hay regla que hacer cumplir. Pero una
   tilde MAL PUESTA (CLAÚSULA) si es un error, y ahi la palabra ya trae tilde.

2. Las sugerencias NO las da hunspell. Su busqueda tarda hasta 11 s en una sola
   palabra larga y deformada. Para la tilde mal puesta la correccion es exacta
   (la misma palabra sin el acento equivocado) y para el resto va rapidfuzz.

  python3 ortografia.py documento.docx
"""
import argparse
import sys
import unicodedata
import urllib.request
from functools import lru_cache
from pathlib import Path

from rapidfuzz import fuzz, process

DIC = Path.home() / ".cache" / "notaria-ocr" / "es_PE"
URL = "https://raw.githubusercontent.com/LibreOffice/dictionaries/master/es/es_PE"
LISTA = Path(__file__).parent / "lista_notarial.txt"

VOCALES = "aeiou"
AGUDA = dict(zip(VOCALES, "áéíóú"))


def _descargar():
    DIC.parent.mkdir(parents=True, exist_ok=True)
    for ext in (".aff", ".dic"):
        if not DIC.with_suffix(ext).exists():
            print(f"  descargando diccionario{ext}…", file=sys.stderr)
            urllib.request.urlretrieve(URL + ext, DIC.with_suffix(ext))


@lru_cache(maxsize=1)
def diccionario():
    """(hunspell, lemas). Cacheado: cargarlo cuesta 0.3 s y 55 MB."""
    from spylls.hunspell import Dictionary
    _descargar()
    d = Dictionary.from_files(str(DIC))
    return d, [w.stem for w in d.dic.words]


def plano(t: str) -> str:
    d = unicodedata.normalize("NFKD", t)
    return "".join(c for c in d if not unicodedata.combining(c)).lower()


def tildada(w: str) -> bool:
    return any(unicodedata.combining(c) for c in unicodedata.normalize("NFKD", w))


def lista_casa() -> set[str]:
    """Terminos que el diccionario general no trae pero la notaria usa."""
    if not LISTA.exists():
        return set()
    return {l.split("#")[0].strip().upper() for l in LISTA.read_text(encoding="utf-8").splitlines()
            if l.split("#")[0].strip()}


def agregar_a_lista(palabras) -> int:
    """Guarda terminos aceptados. Devuelve cuantos se agregaron de verdad."""
    ya = lista_casa()
    nuevas = sorted({p.strip().upper() for p in palabras if p.strip()} - ya)
    if nuevas:
        with LISTA.open("a", encoding="utf-8") as f:
            if not LISTA.stat().st_size:
                f.write("# Terminos aceptados por la notaria: siglas, juridico, toponimos.\n")
            f.write("\n".join(nuevas) + "\n")
    return len(nuevas)


def revisar(texto: str, extra: set[str] = frozenset()) -> list[tuple[str, str, str]]:
    """[(palabra, motivo, sugerencia)] de lo que no es castellano valido.

    `extra` son palabras a dar por buenas ademas de la lista: los nombres de las
    partes, que ya valida la capa de reglas contra el DNI y la minuta.
    """
    d, lemas = diccionario()
    aceptadas = lista_casa() | {e.upper() for e in extra}
    import re
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
            if any(d.lookup(v) or d.lookup(v.upper())
                   for i, c in enumerate(base) if c in VOCALES
                   for v in [base[:i] + AGUDA[c] + base[i + 1:]]):
                continue
        elif d.lookup(base) or d.lookup(base.upper()):
            fuera.append((w, "tilde mal puesta", base))     # correccion exacta
            continue
        m = process.extractOne(base, lemas, scorer=fuzz.ratio)
        fuera.append((w, "no existe en castellano", m[0] if m and m[1] >= 75 else "?"))
    return fuera


def main():
    from extraer import leer
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("documento")
    a = ap.parse_args()
    hallazgos = revisar(leer(Path(a.documento)))
    for w, motivo, sug in hallazgos:
        print(f"  «{w}» {motivo}   ¿{sug}?")
    print(f"\n{len(hallazgos)} palabras marcadas · lista de la casa: {len(lista_casa())} terminos")
    return 1 if hallazgos else 0


if __name__ == "__main__":
    sys.exit(main())
