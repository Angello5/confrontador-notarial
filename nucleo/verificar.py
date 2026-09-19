"""Reglas deterministas de confrontación sobre texto y estructuras."""

import re
import unicodedata

from rapidfuzz import fuzz, process

IMGS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}

RELLENO = re.compile(r"[=_.]{3,}|(?:-?/@/\s*)+")


def norm(t: str) -> str:
    # NFKD antes de upper: 'Nº' -> 'No' minuscula si se invierte el orden
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c)).upper()
    return re.sub(r"\s+", " ", RELLENO.sub(" ", t)).strip()


RE_CUI = re.compile(r"\b(\d{8})\s*-\s*\d\b")
# CUI del RENIEC: 8 digitos + guion + verificador. El watermark (sello) no lo trae.

RE_DNI_DOC = re.compile(
    r"(?:DNI|IDENTIDAD|D[.]N[.]I[.]?)"
    r"\s*(?:(?:N[O°]?|NUMERO)\s*)?(?:[:.]\s*)?(\d{6,9})"
)
# En documentos el DNI viene rotulado; aceptamos 6-9 digitos para cazar los mal escritos.

RE_PARTIDA = re.compile(r"PARTIDA\s*(?:ELECTRONICA\s*)?N[O°]?\s*(\d{5,})")
# La forma corta PARTIDA N° también es valida en algunos actos.

RE_MONTO = re.compile(r"S/\s*(\d[\d,]*\.\d{2})")

RE_NOMBRE = re.compile(
    r"([A-Z][A-Z ]{8,60}?)[,.]{0,2}-?\s*(?:DE\s+)?NACIONALIDAD"
    r"|CASAD[AO]\s+CON\s+([A-Z][A-Z ]{8,60}?)[,.]"
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
    for a, b in RE_NOMBRE.findall(t):
        w = [x for x in (a or b).split() if x not in STOP and len(x) > 1]
        if 2 <= len(w) <= 5:
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


def catalogo(fuentes: dict[str, str]) -> dict[str, set[str]]:
    cat = {"NOMBRE": set(), "DNI": set(), "PARTIDA": set(), "MONTO": set()}
    for nom, raw in fuentes.items():
        t = norm(raw)
        nombre = nom.rsplit("/", 1)[-1]
        sufijo = re.search(r"(?<!^)(\.[^.]*)$", nombre)
        es_img = bool(sufijo and sufijo.group(1).lower() in IMGS)
        cat["DNI"] |= set(RE_CUI.findall(t)) if es_img else set(RE_DNI_DOC.findall(t))
        cat["PARTIDA"] |= set(RE_PARTIDA.findall(t))
        cat["MONTO"] |= set(RE_MONTO.findall(t))
        if es_img:
            if n := nombre_reniec(raw):
                cat["NOMBRE"].add(n)
        else:
            cat["NOMBRE"] |= set(nombres(t))
    return cat


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
    for linea in map(norm, destino.splitlines()):
        if not (4 < len(linea) < 60) or linea in vistos["NOMBRE"]:
            continue
        cand = linea.rstrip(",.")
        if not 2 <= len(cand.split()) <= 5 or not cand.replace(" ", "").isalpha():
            continue
        m = process.extractOne(cand, cat["NOMBRE"], scorer=fuzz.ratio)
        if m and 80 <= m[1] < 100:
            obs.append(f"[NOMBRE] «{cand}» debe decir «{m[0]}»   (caratula)")
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
