"""F21: aplica la carga útil de corrección a una copia de un .docx.

Biblioteca estándar, como la extracción: solo se reescriben los ``w:t`` que
tocan una corrección; el resto del paquete se copia byte a byte (P-04).
"""

import re
import zipfile
from bisect import bisect_right
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


def aplicar(origen, destino, correcciones):
    """Genera ``destino`` con las correcciones; devuelve (aplicadas, no_aplicadas)."""
    origen, destino = Path(origen), Path(destino)
    if origen.resolve() == destino.resolve():
        raise ValueError("El corregido debe ser un archivo distinto del original.")
    with zipfile.ZipFile(origen) as z:
        xml = z.read(DOCUMENTO).decode("utf-8")
        nodos = _nodos(xml)
        parrafos = _parrafos(nodos)
        textos = ["".join(n[2] for n in p) for p in parrafos]
        aplicadas, no_aplicadas, tramos = [], [], []
        for correccion in correcciones:
            ocurrencias = [
                (indice, a, b)
                for indice, texto in enumerate(textos)
                for a, b in coincidencias(texto, correccion["erroneo"])
            ]
            k = correccion["ocurrencia"]
            tramo = ocurrencias[k] if k < len(ocurrencias) else None
            if tramo is None or any(
                t[0] == tramo[0] and t[1] < tramo[2] and tramo[1] < t[2]
                for t, _ in tramos
            ):
                no_aplicadas.append(correccion["id"])
                continue
            tramos.append((tramo, correccion["correcto"]))
            aplicadas.append(correccion["id"])
        # De derecha a izquierda: los índices pendientes siguen valiendo.
        for (indice, a, b), nuevo in sorted(tramos, reverse=True):
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
