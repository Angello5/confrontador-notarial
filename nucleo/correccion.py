"""F21: capa de corrección. De los «debe decir» del núcleo a una carga útil trazable."""

import hashlib
import re
import unicodedata

SEPARADOR_PAGINA = "\f"  # el mismo de nucleo.verificar; la pureza prohíbe importarlo
_RE_DEBE_DECIR = re.compile(
    r"^\[(?P<campo>[^]]+)\]\s+«(?P<erroneo>[^»]*)»\s+debe decir\s+«(?P<correcto>[^»]*)»"
)
# Su «debe decir» es la cifra, no un texto que reemplace al erróneo (FR-005).
_SIN_TEXTO_CORRECTO = {
    "NUMERO_EN_LETRAS",
    "AREA",
    "CORRELATIVO",
    "COPROPIEDAD",
    "DOMICILIO_FISCAL",
}
# F30: reemplazar «CUARTA» o «50%» en todo el documento cambiaría texto ajeno.
# F35: el domicilio de la ficha RUC viene en formato SUNAT, no en la redacción notarial.
# F66: salvo letras mal escritas que, reparadas, valen lo mismo que su cifra: no
# hay nada que decidir y el texto correcto sale del propio borrador, no de una fuente.
_LETRAS_REPARABLES = {"NUMERO_EN_LETRAS", "AREA"}
_RE_LETRAS_MAL_ESCRITAS = re.compile(
    r"\(letras mal escritas; se sugiere «(?P<sugerido>[^»]*)»\)\s*$"
)
_FUENTE_CIFRA = {"archivo": "Cifra del propio borrador", "pagina": None}
_PALABRA = "A-ZÑ0-9"


def _plano(texto: str) -> tuple[str, list[int]]:
    """Mayúsculas, sin tildes (salvo la Ñ) y espacios simples, como ``norm``;
    con el índice del carácter crudo del que sale cada carácter."""
    chars, indices = [], []
    for i, c in enumerate(texto):
        if c.isspace():
            if chars and chars[-1] != " ":
                chars.append(" ")
                indices.append(i)
            continue
        for d in unicodedata.normalize("NFKD", c):
            if d == "\N{COMBINING TILDE}" and chars and chars[-1] == "N":
                chars[-1] = "Ñ"
            elif not unicodedata.combining(d):
                for u in d.upper():
                    chars.append(u)
                    indices.append(i)
    return "".join(chars), indices


def coincidencias(texto: str, valor: str) -> list[tuple[int, int]]:
    """Posiciones crudas de ``valor`` en ``texto`` con límites de palabra."""
    buscado = _plano(valor)[0].strip()
    if not buscado:
        return []
    plano, indices = _plano(texto)
    patron = rf"(?<![{_PALABRA}]){re.escape(buscado)}(?![{_PALABRA}])"
    return [
        (indices[m.start()], indices[m.end()] if m.end() < len(plano) else len(texto))
        for m in re.finditer(patron, plano)
    ]


def marcas(segmentos, valor) -> list[dict]:
    """F32: rectángulos de cada aparición de ``valor`` sobre una página.

    ``segmentos``: ``(texto, x0, y0, x1, y1, linea, bordes)`` en orden de
    lectura, con coordenadas en fracciones de la página; los de la misma
    ``linea`` se unen con espacio y las líneas con salto. ``bordes``: el borde
    izquierdo de cada carácter y el derecho del último (F52). Busca con
    ``coincidencias``.
    """
    partes, tramos, previa = [], [], None
    desplazamiento = 0
    for texto, _x0, y0, _x1, y1, linea, bordes in segmentos:
        if partes:
            sep = " " if linea == previa else "\n"
            partes.append(sep)
            desplazamiento += len(sep)
        partes.append(texto)
        tramos.append((desplazamiento, desplazamiento + len(texto), y0, y1, bordes))
        desplazamiento += len(texto)
        previa = linea
    pagina = "".join(partes)

    resultado = []
    for aparicion, (inicio, fin) in enumerate(coincidencias(pagina, valor or "")):
        while fin > inicio and pagina[fin - 1].isspace():
            fin -= 1
        for desde, hasta, y0, y1, bordes in tramos:
            if hasta <= inicio or desde >= fin:
                continue
            resultado.append(
                {
                    "x0": round(bordes[max(inicio, desde) - desde], 4),
                    "y0": round(y0, 4),
                    "x1": round(bordes[min(fin, hasta) - desde], 4),
                    "y1": round(y1, 4),
                    "aparicion": aparicion,
                }
            )
    return resultado


def _palabras(texto: str) -> str:
    return " " + " ".join(re.findall(f"[{_PALABRA}]+", _plano(texto)[0])) + " "


def correcciones(salidas, fuentes) -> list[dict]:
    """Carga útil: solo «debe decir» con correcto distinto, no truncado y con fuente."""
    paginas = [
        (nombre.rsplit("/", 1)[-1], numero, _palabras(pagina))
        for nombre, texto in fuentes.items()
        for numero, pagina in enumerate(texto.split(SEPARADOR_PAGINA), 1)
    ]
    carga, vistos = [], set()
    for salida in salidas:
        m = _RE_DEBE_DECIR.match(salida) if isinstance(salida, str) else None
        if not m:
            continue
        campo, erroneo, correcto = m["campo"], m["erroneo"], m["correcto"]
        reparadas = (
            _RE_LETRAS_MAL_ESCRITAS.search(salida)
            if campo in _LETRAS_REPARABLES
            else None
        )
        if reparadas:
            correcto = reparadas["sugerido"]
        elif campo in _SIN_TEXTO_CORRECTO:
            continue
        par = (_plano(erroneo)[0].strip(), _plano(correcto)[0].strip())
        # Igual (P-03) o prefijo propio: el reemplazo truncaría el texto.
        # Un par repetido es una sola fila: se aplica a todas las apariciones.
        if par[0].startswith(par[1]) or par in vistos:
            continue
        buscado = _palabras(correcto)
        fuente = (
            dict(_FUENTE_CIFRA)
            if reparadas
            else next(
                (
                    {"archivo": archivo, "pagina": numero}
                    for archivo, numero, palabras in paginas
                    if buscado.strip() and buscado in palabras
                ),
                None,
            )
        )
        if fuente is None:
            continue
        vistos.add(par)
        clave = f"{campo}|{erroneo}|{correcto}".encode()
        carga.append(
            {
                "id": hashlib.sha256(clave).hexdigest()[:12],
                "campo": campo,
                "erroneo": erroneo,
                "correcto": correcto,
                "fuente": fuente,
            }
        )
    return carga
