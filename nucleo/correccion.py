"""F21: capa de corrección. De los «debe decir» del núcleo a una carga útil trazable."""

import hashlib
import re
import unicodedata

SEPARADOR_PAGINA = "\f"  # el mismo de nucleo.verificar; la pureza prohíbe importarlo
_RE_DEBE_DECIR = re.compile(
    r"^\[(?P<campo>[^]]+)\]\s+«(?P<erroneo>[^»]*)»\s+debe decir\s+«(?P<correcto>[^»]*)»"
)
# Su «debe decir» es la cifra, no un texto que reemplace al erróneo (FR-005).
_SIN_TEXTO_CORRECTO = {"NUMERO_EN_LETRAS", "AREA", "CORRELATIVO", "COPROPIEDAD"}
# F30: reemplazar «CUARTA» o «50%» en todo el documento cambiaría texto ajeno.
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
        if not m or m["campo"] in _SIN_TEXTO_CORRECTO:
            continue
        campo, erroneo, correcto = m["campo"], m["erroneo"], m["correcto"]
        par = (_plano(erroneo)[0].strip(), _plano(correcto)[0].strip())
        # Igual (P-03) o prefijo propio: el reemplazo truncaría el texto.
        # Un par repetido es una sola fila: se aplica a todas las apariciones.
        if par[0].startswith(par[1]) or par in vistos:
            continue
        buscado = _palabras(correcto)
        fuente = next(
            (
                {"archivo": archivo, "pagina": numero}
                for archivo, numero, palabras in paginas
                if buscado.strip() and buscado in palabras
            ),
            None,
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
