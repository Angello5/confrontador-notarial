"""Señales técnicas de lectura; no corrige ni interpreta datos jurídicos."""

import math
from statistics import median


VERSION = 3
CONFIANZA_MINIMA = 0.85


def capa_pdf_dudosa(texto):
    if len(texto.strip()) < 50:
        return True
    invalidos = sum(
        c == "\ufffd" or (ord(c) < 32 and c not in "\n\r\t\f") for c in texto
    )
    return invalidos > 0


def resumir(resultado, tol=9):
    textos = list(resultado.txts or ())
    cajas = resultado.boxes if resultado.boxes is not None else ()
    scores = getattr(resultado, "scores", None)
    angulos = [
        math.degrees(math.atan2(b[1][1] - b[0][1], b[1][0] - b[0][0])) for b in cajas
    ]
    # Una marca aislada no puede definir la inclinación del documento.
    dominantes = max(
        ([a for a in angulos if abs(a - centro) <= 3] for centro in angulos),
        key=len,
        default=[],
    )
    angulo = (
        median(dominantes)
        if len(dominantes) >= 3 and len(dominantes) >= len(angulos) * 0.6
        else 0
    )
    if abs(angulo) > 15:
        angulo = 0
    rad = math.radians(angulo)
    cos, sin = math.cos(rad), math.sin(rad)
    aceptadas, descartadas = [], []
    for i, (texto, caja) in enumerate(zip(textos, cajas)):
        puntos = [[float(x), float(y)] for x, y in caja]
        girados = [[x * cos + y * sin, -x * sin + y * cos] for x, y in puntos]
        (x0, y0), (x1, y1) = girados[:2]
        if abs(y1 - y0) > max(4, abs(x1 - x0) * 0.08):
            descartadas.append({"puntos": puntos, "motivo": "inclinacion"})
            continue
        score = float(scores[i]) if scores is not None and i < len(scores) else None
        if score is not None and (not math.isfinite(score) or not 0 <= score <= 1):
            score = None
        aceptadas.append(
            {
                "texto": texto,
                "puntos": puntos,
                "confianza": score,
                "fila": sum(p[1] for p in girados) / 4,
                "columna": min(p[0] for p in girados),
            }
        )
    aceptadas.sort(key=lambda c: c["fila"])
    filas = []
    for caja in aceptadas:
        if not filas or caja["fila"] - filas[-1][0]["fila"] > tol:
            filas.append([])
        filas[-1].append(caja)
    texto = "\n".join(
        "  ".join(c["texto"] for c in sorted(f, key=lambda c: c["columna"]))
        for f in filas
    )
    conocidas = [c for c in aceptadas if c["confianza"] is not None]
    peso = sum(max(1, len(c["texto"])) for c in conocidas)
    confianza = (
        sum(c["confianza"] * max(1, len(c["texto"])) for c in conocidas) / peso
        if peso
        else None
    )
    motivos = []
    if not texto.strip():
        motivos.append("sin_texto")
    elif len(aceptadas) < 3 or sum(c.isalnum() for c in texto) < 25:
        motivos.append("lectura_escasa")
    if confianza is None:
        motivos.append("confianza_no_disponible")
    elif confianza < CONFIANZA_MINIMA or any(c["confianza"] < 0.65 for c in conocidas):
        motivos.append("baja_confianza")
    for caja in aceptadas:
        caja.pop("fila")
        caja.pop("columna")
    return {
        "texto": texto,
        "metodo": "ocr",
        "confianza": confianza,
        "requiere_revision": bool(motivos),
        "motivos": motivos,
        "cajas": aceptadas,
        "cajas_descartadas": len(descartadas),
        "descartadas": descartadas,
        "inclinacion": round(angulo, 2),
        "intentos": 1,
        "transformacion": {"giro": 0, "escala": 1},
    }


def horizontal(informe):
    """Proporción de cajas más anchas que altas.

    RapidOCR gira las cajas altas antes de reconocerlas: una hoja de lado
    también «se lee», pero con las líneas desordenadas.
    """
    cajas = informe.get("cajas") or []
    if not cajas:
        return 0
    anchas = sum(
        math.dist(*c["puntos"][:2]) > math.dist(c["puntos"][0], c["puntos"][3])
        for c in cajas
    )
    return anchas / len(cajas)


def puntuacion(informe):
    """Prefiere lectura respaldada por confianza, sin concatenar alternativas."""
    letras = sum(c.isalnum() for c in informe["texto"])
    confianza = informe["confianza"]
    return (confianza or 0) * min(letras, 500)
