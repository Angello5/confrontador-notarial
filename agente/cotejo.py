"""Cotejo determinista entre documentos: lo exacto lo calcula el código, no el modelo."""

import re

from django.conf import settings

_NUM = r"(\d[\d.,]{0,14})"  # acotado: sin retroceso cuadrático con textos hostiles
AREA = re.compile(r"(?<![\d.,])" + _NUM + r"\s*(?:m2|m²|mt2|metros\s+cuadrados)", re.I)
PARTIDA = re.compile(
    r"partida\s*(?:electr[oó]nica)?\s*(?:n[°º.o]*)?\s*:?\s*(\d{6,})", re.I
)
MONTO = re.compile(r"(S/\.?|US\$|\$)\s*" + _NUM)
SENALES = {
    "hipoteca": r"hipotec",
    "embargo/medida cautelar": r"embargo|medida\s+cautelar|anotaci[oó]n\s+de\s+demanda",
    "pago en efectivo": r"en\s+efectivo",
    "apoderado/poder": r"apoderad|poder\s",
    "casado/conviviente": r"casad[oa]|conviviente",
}


def _valores(rx, texto):
    for m in rx.findall(texto):
        try:
            yield _numero(m)
        except ValueError:
            continue  # «1.2.3» u otro texto que no es un número


def _numero(txt):
    # «1,200.50» y «1.200,50» → 1200.5; «120,50» → 120.5; «1,200» → 1200
    txt = re.sub(r"[.,](?=\d{3}(?:\D|$))", "", txt)
    return float(txt.replace(",", "."))


def _por_documento(documentos):
    datos = {}
    for d in documentos:
        t = d["texto"][: settings.AGENTE_MAX_CONTEXTO]  # mismo tope que el contexto
        datos[d["nombre"]] = {
            "áreas (m²)": set(_valores(AREA, t)),
            "partidas": set(PARTIDA.findall(t)),
            "montos": {f"{m[0]} {m[1]}" for m in MONTO.findall(t)},
            "señales": [k for k, rx in SENALES.items() if re.search(rx, t, re.I)],
        }
    return datos


def cotejar(documentos):
    """Texto con los datos de cada documento y las discrepancias entre ellos."""
    if not documentos:
        return ""
    datos = _por_documento(documentos)
    lineas = ["Por documento:"]
    for nombre, d in datos.items():
        vistos = [
            f"{c}: {', '.join(sorted(map(str, v)))}"
            for c, v in d.items()
            if c != "señales" and v
        ]
        if d["señales"]:
            vistos.append("señales: " + ", ".join(d["señales"]))
        lineas.append(f"- {nombre}: " + ("; ".join(vistos) or "sin datos reconocidos"))
    lineas.append("Discrepancias:")
    hallazgos = []
    for campo in ("áreas (m²)", "partidas"):
        con_dato = {n: d[campo] for n, d in datos.items() if d[campo]}
        comunes = set.intersection(*con_dato.values()) if con_dato else set()
        if len(con_dato) >= 2 and not comunes:
            detalle = "; ".join(
                f"{n}: {', '.join(sorted(map(str, v)))}" for n, v in con_dato.items()
            )
            hallazgos.append(f"- {campo} no coinciden entre documentos ({detalle}).")
    return "\n".join(lineas + (hallazgos or ["- Ninguna en áreas ni partidas."]))
