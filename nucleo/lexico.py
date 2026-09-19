"""Reglas léxicas deterministas sobre texto y vocabulario recibidos."""

import re
import unicodedata
from collections import Counter

from rapidfuzz import fuzz, process

PALABRA = re.compile(r"[^\W\d_]{3,}")

# El castellano solo lleva acento agudo, dieresis en u y la eñe. Un acento grave
# o circunflejo sobre una vocal no es estilo de la casa: es una tecla equivocada.
TILDE_IMPOSIBLE = re.compile(r"[àèìòùÀÈÌÒÙâêîôûÂÊÎÔÛãõÃÕ]")

ACENTO_CORRECTO = str.maketrans("àèìòùÀÈÌÒÙâêîôûÂÊÎÔÛãõÃÕ", "áéíóúÁÉÍÓÚáéíóúÁÉÍÓÚaoAO")

# Ordinales de clausula: conjunto cerrado; se aceptan ambas grafias porque las
# escrituras firmadas usan las dos.
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


def erratas(
    texto: str, vocab: Counter, umbral: int = 82
) -> list[tuple[str, str, float]]:
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
