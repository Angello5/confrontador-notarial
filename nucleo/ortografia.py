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


def _falta(w: str, d, lemas: list[str], aceptadas: set[str]):
    """(palabra, motivo, sugerencia) si ``w`` no es castellano válido; si no, None."""
    # la minúscula intercalada la reporta redaccion, sin límite de largo (lA).
    # Se consulta TAL CUAL antes que en minúscula: hunspell acepta el nombre
    # propio solo capitalizado (Peru falla, Perú y PERÚ pasan) y el documento
    # notarial ya viene en mayúsculas
    if _mezclada(w) or w.upper() in aceptadas or d.lookup(w) or d.lookup(w.lower()):
        return None
    if (aguda := w.translate(_GRAVES)) != w:
        return (w, "acento grave", aguda)  # corrección exacta
    base = plano(w)
    if tildada(w):
        if d.lookup(base) or d.lookup(base.upper()):
            return (w, "tilde mal puesta", base)  # corrección exacta
    elif any(
        d.lookup(v) or d.lookup(v.upper())
        for i, c in enumerate(base)
        if c in VOCALES
        for v in [base[:i] + AGUDA[c] + base[i + 1 :]]
    ):
        # sin tilde: si alguna forma tildada existe, es la convención de mayúsculas
        return None
    m = process.extractOne(base, lemas, scorer=fuzz.ratio)
    return (w, "no existe en castellano", m[0] if m and m[1] >= 75 else "?")


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
    sin_iniciales = _RE_ENTRE_BARRAS.sub("/", texto)
    palabras = dict.fromkeys(re.findall(rf"{_LETRAS}{{3,}}", sin_iniciales))
    return [f for w in palabras if (f := _falta(w, d, lemas, aceptadas))]


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
_GRAMATICALES = frozenset(
    "EL LA LOS LAS LO UNA UN DEL DE AL A EN CON POR PARA SIN SOBRE QUE SE SUS SU NI"
    " Y E O U".split()
)
_REGLAS = (
    (rf"\b({_PALABRA}+)[^\S\n]+(\1)\b", "palabra repetida"),
    (rf"{_PALABRA}+ +(?:[,;:]|\.(?!\.))", "espacio antes de signo"),
    (rf"\b(EL|DEL|AL|LA)[^\S\n]+({_PALABRA}+)\b", "concordancia de artículo"),
)


def _sugerencia(motivo: str, m) -> str | None:
    """Corrección de cada regla cerrada; None si la coincidencia no es error."""
    if motivo == "palabra repetida":
        return m[1] if m[1].upper() in _GRAMATICALES else None
    if motivo == "espacio antes de signo":
        return m[0].split()[0] + m[0][-1]
    articulo, nombre = m[1].upper(), plano(m[2]).upper()
    if nombre not in (_MASCULINOS if articulo == "LA" else _FEMENINOS):
        return None
    correcto = _CORRECTO[articulo]
    return f"{correcto if m[1].isupper() else correcto.lower()} {m[2]}"


def _mezcladas(texto: str) -> list[tuple]:
    """(inicio, fin, palabra, motivo, sugerencia) de cada minúscula intercalada.

    La mayúscula solo se sugiere si la palabra ya existe así en el texto.
    """
    palabras = set(re.findall(rf"{_LETRAS}+", texto))
    return [
        (*m.span(), m[0], "mayúsculas y minúsculas mezcladas", m[0].upper())
        if m[0].upper() in palabras
        else (*m.span(), m[0], "mayúsculas y minúsculas mezcladas", "?")
        for m in re.finditer(rf"{_LETRAS}+", texto)
        if _mezclada(m[0])
    ]


_CIERRE = {"(": ")", "«": "»", "“": "”", '"': '"'}


def _comilla(c: str) -> str:
    return f"comilla recta {c}" if c == '"' else f"comilla {c}"


def _ventana(linea: str, i: int) -> tuple[int, int]:
    """Unos 60 caracteres alrededor de ``i`` sin cortar palabras."""
    fin = linea.find(" ", i + 40)
    return linea.rfind(" ", 0, max(0, i - 20)) + 1, fin if fin >= 0 else len(linea)


def _sin_cerrar(linea: str):
    """F58: (signo, inicio, fin, motivo, sugerencia) de cada signo sin pareja.

    El tramo va del signo a su cierre equivocado o, si no tiene cierre, es una
    ventana corta alrededor del signo. Tras otra comilla abierta, la recta
    seguida de letra o cifra abre una anidada; si no, cierra la abierta.
    """
    parentesis, comillas = [], []
    for i, c in enumerate(linea):
        abre_recta = not comillas or (
            linea[comillas[-1]] != '"' and linea[i + 1 : i + 2].isalnum()
        )
        if c == "(":
            parentesis.append(i)
        elif c == ")" and parentesis:
            parentesis.pop()
        elif c in "«“" or (c == '"' and abre_recta):
            comillas.append(i)
        elif c in '"”»' and comillas:
            j = comillas.pop()
            if c != (cierre := _CIERRE[linea[j]]):
                # inequívoca si el cierre correcto no llega antes de otra apertura
                otro = cierre in linea[i:].split(linea[j])[0]
                motivo = f"{_comilla(linea[j])} cerrada con {_comilla(c)}"
                yield j, j, i + 1, motivo, "?" if otro else linea[j:i] + cierre
    for j in parentesis + comillas:
        falta = "el paréntesis" if linea[j] == "(" else "la comilla"
        yield j, *_ventana(linea, j), f"falta cerrar {falta}", "?"


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
    hallazgos = [
        (*m.span(), m[0], motivo, sugerencia)
        for patron, motivo in _REGLAS
        for m in re.finditer(patron, texto, re.I)
        if (sugerencia := _sugerencia(motivo, m)) is not None
    ] + _mezcladas(texto)
    desde = 0
    for linea in texto.splitlines(keepends=True):
        # se compara solo el signo de apertura: un nombre en el tramo no lo oculta
        hallazgos += [
            (desde + signo, desde + signo + 1, linea[a:b].strip(), motivo, sugerencia)
            for signo, a, b, motivo, sugerencia in _sin_cerrar(linea)
        ]
        desde += len(linea)
    return [
        (fragmento, motivo, sugerencia)
        for inicio, fin, fragmento, motivo, sugerencia in sorted(
            hallazgos, key=lambda h: h[:2]
        )
        if not any(inicio < b and a < fin for a, b in tramos)
    ]
