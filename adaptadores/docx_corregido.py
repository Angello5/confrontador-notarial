"""F21: aplica la carga útil de corrección a una copia de un .docx.

Biblioteca estándar, como la extracción: solo se reescriben los ``w:t`` que
tocan una corrección; el resto del paquete se copia byte a byte (P-04).
"""

import re
import zipfile
from bisect import bisect_right
from collections import Counter
from html import unescape
from pathlib import Path
from xml.sax.saxutils import escape

from nucleo.correccion import coincidencias

DOCUMENTO = "word/document.xml"
RE_T = re.compile(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", re.S)
RE_FALLBACK = re.compile(r"<mc:Fallback>.*?</mc:Fallback>", re.S)


def _nodos(xml):
    """Nodos ``w:t`` visibles: [inicio, fin, texto, párrafo], en orden."""
    fallback = [m.span() for m in RE_FALLBACK.finditer(xml)]
    cierres = [m.start() for m in re.finditer("</w:p>", xml)]
    return [
        [m.start(), m.end(), unescape(m.group(1)), bisect_right(cierres, m.start())]
        for m in RE_T.finditer(xml)
        if not any(a <= m.start() < b for a, b in fallback)
    ]


def _parrafos(nodos):
    parrafos = {}
    for nodo in nodos:
        parrafos.setdefault(nodo[3], []).append(nodo)
    return list(parrafos.values())


def _reemplazar(nodos, inicio, fin, nuevo):
    """Escribe ``nuevo`` en el primer nodo del tramo y recorta los siguientes."""
    desplazamiento = 0
    for nodo in nodos:
        texto = nodo[2]
        a, b = desplazamiento, desplazamiento + len(texto)
        desplazamiento = b
        if b <= inicio or a >= fin:
            continue
        cabeza = texto[: inicio - a] + nuevo if a <= inicio else ""
        nodo[2] = cabeza + texto[min(fin, b) - a :]
        nodo.append(True)  # modificado


def _textos(z):
    xml = z.read(DOCUMENTO).decode("utf-8")
    nodos = _nodos(xml)
    parrafos = _parrafos(nodos)
    return xml, nodos, parrafos, ["".join(n[2] for n in p) for p in parrafos]


def _tramos(textos, correcciones):
    """Todas las apariciones de cada corrección: (válidas, en competencia).

    Tramos de correcciones distintas que se solapan no se aplican (no se adivina).
    """
    tramos = sorted(
        (indice, a, b, c["id"], c["correcto"])
        for c in correcciones
        for indice, texto in enumerate(textos)
        for a, b in coincidencias(texto, c["erroneo"])
    )
    grupos = []
    for tramo in tramos:
        grupo = grupos[-1] if grupos else None
        if grupo and grupo[0][0] == tramo[0] and tramo[1] < max(t[2] for t in grupo):
            grupo.append(tramo)
        else:
            grupos.append([tramo])
    validas = [g[0] for g in grupos if len(g) == 1]
    return validas, {t[3] for g in grupos if len(g) > 1 for t in g}


def apariciones(origen, correcciones):
    """Cuántas apariciones corregiría cada corrección: ``{id: n}``."""
    with zipfile.ZipFile(origen) as z:
        textos = _textos(z)[3]
    return dict(Counter(t[3] for t in _tramos(textos, correcciones)[0]))


def aplicar(origen, destino, correcciones):
    """Genera ``destino`` corrigiendo todas las apariciones.

    Devuelve (``{id: apariciones aplicadas}``, ids no aplicados en algún tramo).
    """
    origen, destino = Path(origen), Path(destino)
    if origen.resolve() == destino.resolve():
        raise ValueError("El corregido debe ser un archivo distinto del original.")
    with zipfile.ZipFile(origen) as z:
        xml, nodos, parrafos, textos = _textos(z)
        validas, en_competencia = _tramos(textos, correcciones)
        cuenta = Counter(t[3] for t in validas)
        aplicadas = {c["id"]: cuenta[c["id"]] for c in correcciones if cuenta[c["id"]]}
        no_aplicadas = [
            c["id"]
            for c in correcciones
            if c["id"] not in aplicadas or c["id"] in en_competencia
        ]
        # De derecha a izquierda: los índices pendientes siguen valiendo.
        for indice, a, b, _, nuevo in reversed(validas):
            _reemplazar(parrafos[indice], a, b, nuevo)
        partes, cursor = [], 0
        for inicio, fin, texto, *resto in nodos:
            if len(resto) > 1:
                partes += [xml[cursor:inicio], '<w:t xml:space="preserve">']
                partes += [escape(texto), "</w:t>"]
                cursor = fin
        partes.append(xml[cursor:])
        with zipfile.ZipFile(destino, "w") as salida:
            for info in z.infolist():
                datos = z.read(info)
                if info.filename == DOCUMENTO:
                    datos = "".join(partes).encode("utf-8")
                salida.writestr(info, datos)
    return aplicadas, no_aplicadas
