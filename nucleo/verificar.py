"""Reglas deterministas de confrontación sobre texto y estructuras."""

import re
import unicodedata
from collections import namedtuple
from collections.abc import Mapping

from rapidfuzz import fuzz, process

IMGS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
SEPARADOR_PAGINA = "\f"


Procedencia = namedtuple("Procedencia", "fuente pagina")
Pagina = namedtuple("Pagina", "fuente numero texto")
PaginaDescartada = namedtuple("PaginaDescartada", "fuente pagina tipo")


class Persona(namedtuple("PersonaBase", "nombre documento procedencias estado")):
    __slots__ = ()

    def __new__(cls, nombre, documento, procedencias, estado="CONFIRMADA"):
        return super().__new__(cls, nombre, documento, procedencias, estado)


class Catalogo(Mapping[str, frozenset[str]]):
    """Resultado puro con una vista histórica calculada, no almacenada."""

    __slots__ = (
        "personas",
        "partidas",
        "montos",
        "paginas_descartadas",
        "paginas_no_clasificadas",
        "_fijo",
    )

    def __init__(
        self,
        personas,
        partidas=frozenset(),
        montos=frozenset(),
        paginas_descartadas=(),
        paginas_no_clasificadas=(),
    ):
        object.__setattr__(self, "personas", tuple(personas))
        object.__setattr__(self, "partidas", frozenset(partidas))
        object.__setattr__(self, "montos", frozenset(montos))
        object.__setattr__(self, "paginas_descartadas", tuple(paginas_descartadas))
        object.__setattr__(
            self, "paginas_no_clasificadas", tuple(paginas_no_clasificadas)
        )
        object.__setattr__(self, "_fijo", True)

    def __setattr__(self, campo, valor):
        if hasattr(self, "_fijo"):
            raise AttributeError("Catalogo es de solo lectura")
        object.__setattr__(self, campo, valor)

    def __getitem__(self, campo: str) -> frozenset[str]:
        if campo == "NOMBRE":
            return frozenset(p.nombre for p in self.personas if p.nombre)
        if campo == "DNI":
            return frozenset(p.documento for p in self.personas if p.documento)
        if campo == "PARTIDA":
            return self.partidas
        if campo == "MONTO":
            return self.montos
        raise KeyError(campo)

    def __iter__(self):
        return iter(("NOMBRE", "DNI", "PARTIDA", "MONTO"))

    def __len__(self) -> int:
        return 4


RELLENO = re.compile(r"[=_.]{3,}|(?:-?/@/\s*)+")


def norm(t: str) -> str:
    # NFKD antes de upper: 'Nº' -> 'No' minuscula si se invierte el orden
    descompuesto = unicodedata.normalize("NFKD", t)
    sin_combinantes = []
    for c in descompuesto:
        if (
            c == "\N{COMBINING TILDE}"
            and sin_combinantes
            and sin_combinantes[-1] in "Nn"
        ):
            sin_combinantes[-1] = "Ñ"
        elif not unicodedata.combining(c):
            sin_combinantes.append(c)
    t = "".join(sin_combinantes).upper()
    return re.sub(r"\s+", " ", RELLENO.sub(" ", t)).strip()


RE_CUI = re.compile(r"\b(\d{8})\s*-\s*\d\b")
# CUI del RENIEC: 8 digitos + guion + verificador. El watermark (sello) no lo trae.

RE_DNI_DOC = re.compile(
    r"(?:DNI|IDENTIDAD|D[.]N[.]I[.]?)"
    r"\s*(?:(?:N[O°]?|NUMERO)\s*)?(?:[:.]\s*)?(?<!\d)(\d{8})(?!\d)"
)
# En documentos el DNI viene rotulado y siempre tiene exactamente 8 digitos.

RE_PARTIDA = re.compile(r"PARTIDA\s*(?:ELECTRONICA\s*)?N[O°]?\s*(\d{5,})")
# La forma corta PARTIDA N° también es valida en algunos actos.

RE_MONTO = re.compile(r"S/\s*(\d[\d,]*\.\d{2})")

RE_NOMBRE = re.compile(
    r"([A-ZÑ][A-ZÑ ]{8,60}?)[,.]{0,2}-?\s*(?:DE\s+)?NACIONALIDAD"
    r"|CASAD[AO]\s+CON\s+([A-ZÑ][A-ZÑ ]{8,60}?)[,.]"
)
# Nombre en mayusculas antes de NACIONALIDAD o despues de CASAD@ CON.

RE_RENIEC = {"nom": "NOMBRES", "pat": "APELLIDO PATERNO", "mat": "APELLIDO MATERNO"}

STOP = {
    "DE",
    "DEL",
    "LA",
    "EL",
    "LOS",
    "LAS",
    "Y",
    "CON",
    "UNA",
    "OTRA",
    "PARTE",
    "CASADA",
    "CASADO",
    "SOLTERA",
    "SOLTERO",
    "QUIEN",
    "SENOR",
    "SEÑOR",
    "NOTARIO",
    "A",
    "FAVOR",
    "QUE",
    "SE",
    "SU",
    "ES",
    "AMBOS",
    "CELEBRAN",
    "OTORGA",
    "PERUANA",
}


def nombres(t: str) -> list[str]:
    out = []
    for a, b in RE_NOMBRE.findall(norm(t)):
        w = [x for x in (a or b).split() if len(x) > 1 or x in STOP]
        while w and w[0] in STOP:
            w.pop(0)
        while w and w[-1] in STOP:
            w.pop()
        if 2 <= len(w) <= 7:
            out.append(" ".join(w))
    return out


def nombre_reniec(raw: str) -> str | None:
    """Arma el nombre desde los rotulos del informe RENIEC (nombres + 2 apellidos).
    Lee por columnas: ocr_lineas separa celdas con dos espacios."""
    c = {}
    for linea in raw.splitlines():
        celdas = [norm(x).rstrip(":") for x in re.split(r"\s{2,}", linea)]
        for i, cel in enumerate(celdas[:-1]):
            for k, etq in RE_RENIEC.items():
                if cel == etq and celdas[i + 1].replace(" ", "").isalpha():
                    c.setdefault(k, celdas[i + 1])
    return f"{c['nom']} {c['pat']} {c['mat']}" if len(c) == 3 else None


_TIPOS_DESCARTADOS = {"BLANCA_SEPARADOR", "SISGEN"}
_MARCAS_SISGEN = (
    "CONSULTA REALIZADA",
    "COINCIDENCIAS",
    "DOCUMENTO IDENTIFICATIVO",
    "N CONSULTA",
)


def clasificar_pagina(texto: str) -> str:
    """Clasifica por marcas estructurales, conservando lo que sea dudoso."""
    t = norm(texto)
    if not t:
        return "BLANCA_SEPARADOR"
    if sum(marca in t for marca in _MARCAS_SISGEN) >= 2:
        return "SISGEN"
    if (RE_CUI.search(t) or "APELLIDO PATERNO" in t) and all(
        etiqueta in t for etiqueta in RE_RENIEC.values()
    ):
        return "RENIEC"
    if "INFORMACION PERSONAL" in t and all(
        etiqueta in t for etiqueta in ("PRIMER APELLIDO", "SEGUNDO APELLIDO", "NOMBRES")
    ):
        return "BIOMETRICA"
    if "DECLARACION JURADA" in t or (
        "APELLIDOS" in t and "NOMBRES" in t and "DOCUMENTO DE IDENTIDAD" in t
    ):
        return "DECLARACION_JURADA"
    if (
        sum(marca in t for marca in ("PARTIDA", "ASIENTO", "CARGO", "IDENTIFICADO CON"))
        >= 2
    ):
        return "SUNARP"
    if "FICHA DE IDENTIDAD" in t or "DOCUMENTO NACIONAL DE IDENTIDAD" in t:
        return "IDENTIDAD"
    if nombres(t) or RE_DNI_DOC.search(t):
        return "PROSA"
    return "DESCONOCIDA"


def _sufijo(nombre: str) -> str | None:
    match = re.search(r"(?<!^)(\.[^.]+)$", nombre)
    return match.group(1).lower() if match else None


def _linea_etiquetada(raw: str, etiqueta: str) -> str | None:
    """Lee campos de formularios sin interpretar números cercanos."""
    for linea in raw.splitlines():
        t = norm(linea)
        if not t.startswith(etiqueta):
            continue
        resto = t[len(etiqueta) :].lstrip(" :")
        if etiqueta == "NOMBRES" and resto.startswith(("Y ", "DEL ")):
            continue
        if resto:
            return resto
    return None


def _nombres_de_pagina(
    raw: str, tipo: str, es_pdf: bool, es_img: bool = False
) -> list[str]:
    t = norm(raw)
    out = list(nombres(t))
    if tipo in {"RENIEC", "BIOMETRICA"}:
        if tipo == "BIOMETRICA":
            n = _linea_etiquetada(raw, "NOMBRES")
            pat = _linea_etiquetada(raw, "PRIMER APELLIDO")
            mat = _linea_etiquetada(raw, "SEGUNDO APELLIDO")
            reniec = " ".join(x for x in (n, pat, mat) if x)
        elif es_img or es_pdf:
            reniec = nombre_reniec(raw)
        else:
            reniec = None
        if reniec:
            out.append(reniec)
    if tipo == "DECLARACION_JURADA":
        apellidos = _linea_etiquetada(raw, "APELLIDOS")
        nombres_campo = _linea_etiquetada(raw, "NOMBRES")
        if apellidos and nombres_campo:
            out.append(f"{nombres_campo} {apellidos}")
        conyuge = _linea_etiquetada(raw, "NOMBRES Y APELLIDOS DEL CONYUGE")
        if conyuge:
            out.append(conyuge)
    if es_pdf and (reniec := nombre_reniec(raw)):
        out.append(reniec)
    return list(dict.fromkeys(out))


def _documentos_de_pagina(raw: str, tipo: str, es_img: bool) -> list[str]:
    if tipo == "SISGEN":
        return []
    limpio = "\n".join(
        linea
        for linea in raw.splitlines()
        if not re.search(
            r"\b(?:OPERADOR|USUARIO|NOTARIO|TRANSACCION|VERIFICACION|RUC|TELEFONO|CORREO)\b",
            norm(linea),
        )
    )
    t = norm(limpio)
    if es_img or tipo == "RENIEC":
        return list(dict.fromkeys(RE_CUI.findall(t)))
    return list(dict.fromkeys(RE_DNI_DOC.findall(t)))


def _personas_de_pagina(pagina: Pagina, tipo: str) -> list[Persona]:
    sufijo = _sufijo(pagina.fuente.rsplit("/", 1)[-1])
    es_img = bool(sufijo and sufijo in IMGS)
    nombres_pagina = _nombres_de_pagina(pagina.texto, tipo, sufijo == ".pdf", es_img)
    documentos = _documentos_de_pagina(pagina.texto, tipo, es_img)
    procedencia = (Procedencia(pagina.fuente, pagina.numero),)
    if len(nombres_pagina) == 1 and len(documentos) == 1:
        return [Persona(nombres_pagina[0], documentos[0], procedencia)]
    personas = [
        Persona(nombre, None, procedencia, "SIN_DOCUMENTO") for nombre in nombres_pagina
    ]
    personas.extend(
        Persona(None, documento, procedencia, "REVISION_MANUAL")
        for documento in documentos
    )
    return personas


def _paginas(fuentes: Mapping[str, str]) -> list[Pagina]:
    return [
        Pagina(nombre, numero, texto)
        for nombre, raw in fuentes.items()
        for numero, texto in enumerate(raw.split(SEPARADOR_PAGINA), 1)
    ]


def catalogo(fuentes: Mapping[str, str]) -> Catalogo:
    personas = []
    partidas = set()
    montos = set()
    descartadas = []
    no_clasificadas = []
    for pagina in _paginas(fuentes):
        t = norm(pagina.texto)
        partidas.update(RE_PARTIDA.findall(t))
        montos.update(RE_MONTO.findall(t))
        tipo = clasificar_pagina(pagina.texto)
        if tipo in _TIPOS_DESCARTADOS:
            descartadas.append(PaginaDescartada(pagina.fuente, pagina.numero, tipo))
            continue
        if tipo == "DESCONOCIDA":
            no_clasificadas.append(PaginaDescartada(pagina.fuente, pagina.numero, tipo))
        personas.extend(_personas_de_pagina(pagina, tipo))
    return Catalogo(
        tuple(personas),
        frozenset(partidas),
        frozenset(montos),
        tuple(descartadas),
        tuple(no_clasificadas),
    )


def correspondencia(cat: dict[str, set[str]], destino: str) -> tuple[float, int]:
    """(cuanto de la fuente reaparece en el destino, cuantos DNI ajenos trae el destino)

    Si un borrador es de OTRO expediente no comparte ningun dato con la fuente y
    ademas trae los suyos propios; comparar campo por campo devuelve cientos de
    filas inutiles. En cambio un anexo legitimo tampoco comparte identidades pero
    no trae DNI ajenos, y ahi no hay que alarmar."""
    d = norm(destino)
    aciertos = total = 0
    for v in cat["DNI"]:
        total += 1
        aciertos += v in d
    candidatos = nombres(d) + [
        norm(linea).rstrip(",.") for linea in destino.splitlines()
    ]
    for v in cat["NOMBRE"]:
        total += 1
        m = process.extractOne(v, candidatos, scorer=fuzz.ratio) if candidatos else None
        aciertos += bool(m and m[1] >= 80)
    ajenos = set(RE_DNI_DOC.findall(d)) - cat["DNI"]
    return (aciertos / total if total else 1.0), len(ajenos)


def diagnostico(fuentes: dict[str, str], destino: str) -> str | None:
    """Aviso de bloqueo cuando no tiene sentido comparar campo por campo.

    Se mide archivo por archivo y se toma el mejor, no el catalogo mezclado: un
    expediente trae fuentes que no llevan identidades (un anexo, una plantilla) y
    promediarlas hunde la cobertura de la minuta, que es la que manda. Se ignoran
    las fuentes sin nombres ni DNI porque no pueden opinar."""
    mejor, ajenos_mejor = (
        -1.0,
        0,
    )  # -1 y no 0: con cobertura 0 hay que registrar los DNI ajenos
    for nombre, texto in fuentes.items():
        cat = catalogo({nombre: texto})
        if not (cat["NOMBRE"] or cat["DNI"]):
            continue  # no lleva identidades: no aporta al juicio
        cob, ajenos = correspondencia(cat, destino)
        if cob > mejor:
            mejor, ajenos_mejor = cob, ajenos
    if mejor >= 0.34:
        return None
    if ajenos_mejor >= 2:
        return (
            f"El borrador no corresponde a estas fuentes: no comparte ningun dato "
            f"identificatorio y trae {ajenos_mejor} DNI distintos. Parece otro "
            f"expediente o una plantilla."
        )
    return (
        "El borrador no repite los nombres ni los DNI de las fuentes. Si es un anexo "
        "o un cronograma es normal; si deberia ser la escritura, revisa los archivos."
    )


def revisar(cat: dict[str, set[str]], destino: str, umbral: int) -> list[str]:
    d = norm(destino)
    obs, vistos = [], {k: set() for k in cat}

    def check(campo, valor, ctx=""):
        vistos[campo].add(valor)
        if valor in cat[campo]:
            return
        m = process.extractOne(valor, cat[campo], scorer=fuzz.ratio)
        esperado = (
            f"debe decir «{m[0]}»"
            if m and m[1] >= 65
            else "no coincide con ninguna fuente"
        )
        obs.append(f"[{campo}] «{valor}» {esperado}{ctx}")

    for n in nombres(d):
        check("NOMBRE", n)
    # la caratula lista los nombres sueltos, sin "DE NACIONALIDAD" que los delate.
    # ponytail: heuristica por linea corta; si aparecen falsos positivos, acotar a
    # las lineas anteriores a "EN LA CIUDAD DE".
    vistos_caratula = set()
    for linea in map(norm, destino.splitlines()):
        if not (4 < len(linea) < 60):
            continue
        cand = linea.rstrip(",.")
        if cand in vistos["NOMBRE"] or cand in vistos_caratula:
            continue
        if not 2 <= len(cand.split()) <= 7 or not cand.replace(" ", "").isalpha():
            continue
        m = process.extractOne(cand, cat["NOMBRE"], scorer=fuzz.ratio)
        if m and 80 <= m[1] < 100:
            obs.append(f"[NOMBRE] «{cand}» debe decir «{m[0]}»   (caratula)")
            vistos_caratula.add(cand)
            vistos["NOMBRE"].add(m[0])
    for m in RE_DNI_DOC.finditer(d):
        check("DNI", m.group(1), f"   …{d[max(0, m.start() - 55) : m.end()][-70:]}")
    for v in RE_PARTIDA.findall(d):
        check("PARTIDA", v)
    for v in RE_MONTO.findall(d):
        check("MONTO", v)

    for campo, vals in cat.items():
        for falta in sorted(vals - vistos[campo]):
            obs.append(
                f"[{campo}] FALTA: «{falta}» esta en las fuentes y no aparece en el destino"
            )
    return obs


def parrafos(t: str) -> list[str]:
    return [p for linea in t.splitlines() if len(p := norm(linea)) > 80]


def revisar_parrafos(minutas: list[str], destino: str, umbral: int) -> list[str]:
    dp = parrafos(destino)
    obs = []
    for src in minutas:
        for p in parrafos(src):
            m = process.extractOne(p, dp, scorer=fuzz.partial_ratio)
            if not m or m[1] < umbral:
                # con dos decimales: a 99.7% redondeado a 0 decimales salia "100%",
                # que se lee como "coincide del todo y aun asi lo marco"
                obs.append(
                    f"[PARRAFO] falta o alterado ({m[1]:.2f}%): {p[:100]}…"
                    if m
                    else f"[PARRAFO] falta: {p[:100]}…"
                )
    return obs
