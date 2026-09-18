"""Detector de erratas por vocabulario, determinista.

La idea: las escrituras YA FIRMADAS por la notaria son el diccionario. Una
palabra que nunca aparecio en ninguna escritura firmada, y que se parece mucho
a una que si, es una errata (OCTAO por OCTAVO). Una palabra rara que ya salio
en escrituras firmadas es vocabulario de la casa, no un error.

Esto cubre el vocabulario CERRADO (ordinales, formulas notariales) sin modelo y
sin varianza. Lo abierto —concordancia, sintaxis— sigue siendo del LLM.

  python3 lexico.py Resultado/ -d "Proyecto(borrador)/...docx"
"""
import argparse
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from rapidfuzz import fuzz, process

from extraer import DOCS, leer

PALABRA = re.compile(r"[^\W\d_]{3,}")

# El castellano solo lleva acento agudo, dieresis en u y la eñe. Un acento grave
# o circunflejo sobre una vocal no es estilo de la casa: es una tecla equivocada
# (OCUPACIÒN). Se detecta sin corpus y sin modelo.
TILDE_IMPOSIBLE = re.compile(r"[àèìòùÀÈÌÒÙâêîôûÂÊÎÔÛãõÃÕ]")
ACENTO_CORRECTO = str.maketrans("àèìòùÀÈÌÒÙâêîôûÂÊÎÔÛãõÃÕ", "áéíóúÁÉÍÓÚáéíóúÁÉÍÓÚaoAO")

# Ordinales de clausula: conjunto cerrado, va aunque el corpus sea chico.
# Se aceptan las dos grafias porque las escrituras firmadas usan las dos.
ORDINALES = """PRIMERO SEGUNDO TERCERO CUARTO QUINTO SEXTO SEPTIMO SÉPTIMO SETIMO
OCTAVO NOVENO DECIMO DÉCIMO UNDECIMO UNDÉCIMO DUODECIMO DUODÉCIMO DECIMOPRIMERO
DECIMOSEGUNDO DECIMOTERCERO VIGESIMO VIGÉSIMO""".split()


def sin_tilde(t: str) -> str:
    d = unicodedata.normalize("NFKD", t)
    return "".join(c for c in d if not unicodedata.combining(c)).upper()


def contar(textos) -> Counter:
    """Vocabulario sin tildes: la notaria escribe la misma palabra con y sin tilde
    en un mismo documento, asi que la tilde no distingue nada."""
    v = Counter(sin_tilde(p) for p in ORDINALES)
    for t in textos:
        v.update(sin_tilde(x) for x in PALABRA.findall(t))
    return v


def vocabulario(rutas: list[str]) -> Counter:
    def archivos():
        for r in rutas:
            p = Path(r)
            yield from (sorted(x for x in p.rglob("*") if x.suffix.lower() in DOCS)
                        if p.is_dir() else [p])
    return contar(leer(a) for a in archivos())


def _es_flexion(p: str, vocab: Counter) -> bool:
    """CLAUSULAS frente a CLAUSULA, o SUSCRITO frente a SUSCRITA, son la misma
    palabra en otro numero o genero: se parecen mucho pero no son erratas. Solo
    se aceptan sufijos de plural y el cambio de vocal final, asi que ZURBELI
    (que necesitaria agregar una A) sigue saliendo marcado."""
    variantes = {p + "S", p + "ES"}
    if p.endswith("S"):
        variantes |= {p[:-1], p[:-2]}
    if p[-1:] in "OAE":
        variantes |= {p[:-1] + v for v in "OAE"}
    return any(v in vocab for v in variantes)


def erratas(texto: str, vocab: Counter, umbral: int = 82) -> list[tuple[str, str, float]]:
    """Palabras con acento imposible, y palabras ausentes del corpus que se
    parecen mucho a una presente."""
    conocidas = list(vocab)
    fuera = []
    for palabra in dict.fromkeys(PALABRA.findall(texto)):
        if TILDE_IMPOSIBLE.search(palabra):
            fuera.append((palabra, palabra.translate(ACENTO_CORRECTO), 100.0))
            continue
        plana = sin_tilde(palabra)
        if plana in vocab:
            continue
        if _es_flexion(plana, vocab):
            continue
        m = process.extractOne(plana, conocidas, scorer=fuzz.ratio)
        if m and m[1] >= umbral:
            fuera.append((plana, m[0], m[1]))
    return sorted(fuera, key=lambda x: -x[2])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("firmadas", nargs="+", help="escrituras ya firmadas (el diccionario)")
    ap.add_argument("-d", "--destino", required=True, help="borrador a revisar")
    ap.add_argument("-u", "--umbral", type=int, default=82)
    a = ap.parse_args()

    vocab = vocabulario(a.firmadas)
    print(f"corpus: {sum(vocab.values())} palabras, {len(vocab)} distintas", file=sys.stderr)
    fuera = erratas(leer(Path(a.destino)), vocab, a.umbral)
    for palabra, cerca, score in fuera:
        print(f"  «{palabra}» no aparece en ninguna escritura firmada"
              f"   ¿querias decir «{cerca}»? ({score:.0f}%)")
    print(f"\n{len(fuera)} palabras sospechosas")
    return 1 if fuera else 0


if __name__ == "__main__":
    sys.exit(main())
