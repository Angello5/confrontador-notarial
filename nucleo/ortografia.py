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
    sin_combinantes = []
    for c in d:
        if (
            c == "\N{COMBINING TILDE}"
            and sin_combinantes
            and sin_combinantes[-1] in "Nn"
        ):
            sin_combinantes[-1] = "Ñ"
        elif not unicodedata.combining(c):
            sin_combinantes.append(c)
    return "".join(sin_combinantes).lower()


def tildada(w: str) -> bool:
    d = unicodedata.normalize("NFKD", w)
    return any(
        unicodedata.combining(c)
        and not (c == "\N{COMBINING TILDE}" and i and d[i - 1] in "Nn")
        for i, c in enumerate(d)
    )


# F39: errores de tipeo. La errata llega como una letra en minuscula dentro de
# la palabra (lA, HIzo, CREDITOz) o con acento grave (SÈTIMA, CLÀUSULA).
_LETRAS = r"[^\W\d_ºª]"  # Nº y 1ª no son palabras
_GRAVES = str.maketrans("àèìòùÀÈÌÒÙ", "áéíóúÁÉÍÓÚ")
# el abogado que autoriza la minuta: nombre propio fuera del A.3 y de las fuentes
_RE_AUTORIZA = re.compile(r"AUTORIZA\s*:\s*([^,\n]{3,80}?)\s*,\s*ABOGAD[OA]", re.I)
# iniciales del digitador en la linea de cierre: «-/@/ -/@/ XYZ / -/@/»
_RE_ENTRE_BARRAS = re.compile(r"/[^\S\n]*[^\W\d_]{2,6}[^\S\n]*(?=/)")


def _mezclada(w: str) -> bool:
    """lA, HIzo, CREDITOz. No: AVENIDA, Avenida, avenida ni marcas como WhatsApp."""
    if w.isupper() or w.islower() or w.istitle():
        return False
    return "".join(re.findall(r"[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+", w)) != w


def revisar(
    texto: str, d, lemas: list[str], lista: set[str], extra: set[str] = frozenset()
) -> list[tuple[str, str, str]]:
    """[(palabra, motivo, sugerencia)] de lo que no es castellano valido.

    `extra` son palabras a dar por buenas ademas de la lista: los nombres de las
    partes, que ya valida la capa de reglas contra el DNI y la minuta.
    """
    aceptadas = lista | {e.upper() for e in extra}
    aceptadas |= {
        p.upper()
        for m in _RE_AUTORIZA.finditer(texto)
        for p in re.findall(rf"{_LETRAS}+", m[1])
    }
    fuera = []
    sin_iniciales = _RE_ENTRE_BARRAS.sub("/", texto)
    for w in dict.fromkeys(re.findall(rf"{_LETRAS}{{3,}}", sin_iniciales)):
        if _mezclada(w):
            continue  # la reporta redaccion, sin limite de largo (lA)
        # se consulta TAL CUAL antes que en minuscula: hunspell acepta el nombre
        # propio solo capitalizado (Peru falla, Perú y PERÚ pasan) y el documento
        # notarial ya viene en mayusculas
        if w.upper() in aceptadas or d.lookup(w) or d.lookup(w.lower()):
            continue
        if (aguda := w.translate(_GRAVES)) != w:
            fuera.append((w, "acento grave", aguda))  # correccion exacta
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


# F23: gramatica y redaccion con reglas cerradas. Lo completo necesita un motor
# linguistico que no esta en el alcance local (spec 017).
_PALABRA = r"[^\W\d_]"
_FEMENINOS = {
    "CLAUSULA", "PARTIDA", "ESCRITURA", "MINUTA",
    "VENDEDORA", "COMPRADORA", "PROPIEDAD", "SOCIEDAD",
}  # fmt: skip
# PARTE no entra: «EL PARTE» notarial es correcto
_MASCULINOS = {"CONTRATO", "INMUEBLE", "PRECIO", "PREDIO", "VENDEDOR", "COMPRADOR"}
_CORRECTO = {"EL": "LA", "DEL": "DE LA", "AL": "A LA", "LA": "EL"}
# Solo palabras gramaticales: LIMA LIMA (provincia y departamento) y ZAFIRO
# ZAFIRO (apellidos iguales) son correctos.
_GRAMATICALES = "EL|LA|LOS|LAS|LO|UNA|UN|DEL|DE|AL|A|EN|CON|POR|PARA|SIN|SOBRE|QUE|SE|SUS|SU|NI|Y|E|O|U"
_REGLAS = (
    (rf"\b({_GRAMATICALES})[^\S\n]+(\1)\b", "palabra repetida"),
    (rf"{_PALABRA}+ +(?:[,;:]|\.(?!\.))", "espacio antes de signo"),
    (rf"\b(EL|DEL|AL|LA)[^\S\n]+({_PALABRA}+)\b", "concordancia de artículo"),
)


def _sin_cerrar(linea: str) -> str | None:
    if linea.count("(") > linea.count(")"):
        return "paréntesis sin cerrar"
    if (
        linea.count('"') % 2
        or linea.count("«") > linea.count("»")
        or linea.count("“") > linea.count("”")
    ):
        return "comillas sin cerrar"
    return None


def redaccion(texto: str, protegidos) -> list[tuple[str, str, str]]:
    """[(fragmento, motivo, sugerencia)] en orden de aparicion.

    Se descarta lo que se solapa con un dato protegido (A.3): la capa
    linguistica no tiene autoridad sobre nombres, DNI, montos ni domicilios.
    """
    tramos = [
        m.span()
        for valor in protegidos
        if (palabras := valor.split())
        for m in re.finditer(r"\s+".join(map(re.escape, palabras)), texto, re.I)
    ]
    hallazgos = []
    for patron, motivo in _REGLAS:
        for m in re.finditer(patron, texto, re.I):
            inicio, fin = m.span()
            fragmento = m[0]
            if motivo == "palabra repetida":
                sugerencia = m[1]
            elif motivo == "espacio antes de signo":
                sugerencia = fragmento.split()[0] + fragmento[-1]
            else:
                articulo, nombre = m[1].upper(), plano(m[2]).upper()
                if articulo == "LA" and nombre not in _MASCULINOS:
                    continue
                if articulo != "LA" and nombre not in _FEMENINOS:
                    continue
                correcto = _CORRECTO[articulo]
                sugerencia = (
                    f"{correcto if m[1].isupper() else correcto.lower()} {m[2]}"
                )
            hallazgos.append((inicio, fin, fragmento, motivo, sugerencia))
    palabras = set(re.findall(rf"{_LETRAS}+", texto))
    for m in re.finditer(rf"{_LETRAS}+", texto):
        w = m[0]
        if _mezclada(w):
            # la mayuscula solo se sugiere si la palabra ya existe asi en el texto
            sugerencia = w.upper() if w.upper() in palabras else "?"
            hallazgos.append(
                (*m.span(), w, "mayúsculas y minúsculas mezcladas", sugerencia)
            )
    desde = 0
    for linea in texto.splitlines(keepends=True):
        if motivo := _sin_cerrar(linea):
            # el tramo es solo el signo de apertura: un nombre en la linea no la oculta
            signo = next(i for i, c in enumerate(linea) if c in '("«“')
            hallazgos.append(
                (desde + signo, desde + signo + 1, linea.strip(), motivo, "?")
            )
        desde += len(linea)
    return [
        (fragmento, motivo, sugerencia)
        for inicio, fin, fragmento, motivo, sugerencia in sorted(
            hallazgos, key=lambda h: h[:2]
        )
        if not any(inicio < b and a < fin for a, b in tramos)
    ]
