"""Reglas deterministas de confrontación sobre texto y estructuras."""

import re
import unicodedata
from collections import Counter, namedtuple
from collections.abc import Mapping
from datetime import date

from rapidfuzz import fuzz, process
from rapidfuzz.distance import Levenshtein

IMGS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
SEPARADOR_PAGINA = "\f"


Procedencia = namedtuple("Procedencia", "fuente pagina")
Pagina = namedtuple("Pagina", "fuente numero texto")
PaginaDescartada = namedtuple("PaginaDescartada", "fuente pagina tipo")


Persona = namedtuple(
    "Persona",
    "nombre documento procedencias estado estado_civil fecha_nacimiento domicilio distrito "
    "procedencia_estado_civil procedencia_fecha_nacimiento procedencia_domicilio procedencia_distrito "
    "fecha_emision emisiones_campos adjuntos conyuge procedencia_conyuge",
    defaults=("CONFIRMADA",) + (None,) * 13,
)


class Catalogo(Mapping[str, frozenset[str]]):
    """Resultado puro con una vista histórica calculada, no almacenada."""

    __slots__ = (
        "personas",
        "partidas",
        "montos",
        "paginas_descartadas",
        "paginas_no_clasificadas",
        "menciones",
        "rucs",
        "direcciones",
        "vocabulario",
        "cantidades",
        "registrales",
        "_fijo",
    )

    def __init__(
        self,
        personas,
        partidas=frozenset(),
        montos=frozenset(),
        paginas_descartadas=(),
        paginas_no_clasificadas=(),
        menciones=(),
        rucs=frozenset(),
        direcciones=frozenset(),
        vocabulario=(),
        cantidades=frozenset(),
        registrales=frozenset(),
    ):
        object.__setattr__(self, "personas", tuple(personas))
        object.__setattr__(self, "partidas", frozenset(partidas))
        object.__setattr__(self, "montos", frozenset(montos))
        object.__setattr__(self, "paginas_descartadas", tuple(paginas_descartadas))
        object.__setattr__(
            self, "paginas_no_clasificadas", tuple(paginas_no_clasificadas)
        )
        object.__setattr__(self, "menciones", tuple(menciones))
        object.__setattr__(self, "rucs", frozenset(rucs))
        # F22: más los domicilios RENIEC ya leídos de las personas.
        object.__setattr__(
            self,
            "direcciones",
            frozenset(direcciones)
            | {norm(p.domicilio) for p in self._registros() if p.domicilio},
        )
        # F22 ronda 2: palabras de las fuentes, para distinguir el ruido OCR.
        object.__setattr__(self, "vocabulario", Counter(vocabulario))
        # F30: (concepto, cifra) y (clase, valor); sin FALTA, por eso no son campos.
        object.__setattr__(self, "cantidades", frozenset(cantidades))
        object.__setattr__(self, "registrales", frozenset(registrales))
        object.__setattr__(self, "_fijo", True)

    def __setattr__(self, campo, valor):
        if hasattr(self, "_fijo"):
            raise AttributeError("Catalogo es de solo lectura")
        object.__setattr__(self, campo, valor)

    def _registros(self):
        for persona in self.personas:
            yield persona
            yield from persona.adjuntos or ()
        yield from self.menciones

    def __getitem__(self, campo: str) -> frozenset[str]:
        if campo == "NOMBRE":
            return frozenset(
                nombre
                for p in self._registros()
                for nombre in (p.nombre, p.conyuge)
                if nombre
            )
        if campo == "DNI":
            return frozenset(p.documento for p in self._registros() if p.documento)
        if campo == "PARTIDA":
            return self.partidas
        if campo == "MONTO":
            return self.montos
        if campo == "RUC":
            return self.rucs
        if campo == "DIRECCION":
            return self.direcciones
        raise KeyError(campo)

    def __iter__(self):
        return iter(("NOMBRE", "DNI", "PARTIDA", "MONTO", "RUC", "DIRECCION"))

    def __len__(self) -> int:
        return 6


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
    r"(?:DNI|IDENTIDAD|D[.]N[.]I[.]?|D[.]N[.]1[,.;]?)"
    r"\s*(?:(?:N[O°]?|NUMERO)\s*)?(?:[:,.]\s*)?(?<!\d)(\d{8})(?!\d)"
)
# En documentos el DNI viene rotulado y siempre tiene exactamente 8 digitos.
RE_DNI_BORRADOR = re.compile(
    r"(?:DNI|IDENTIDAD|D[.]N[.]I[.]?|D[.]N[.]1[,.;]?)"
    r"\s*(?:(?:N[O°]?|NUMERO|NRO[.]?)\s*)?(?:[:,.]\s*)?(?<!\d)(\d{6,10})(?!\d)"
)
# F19: en el borrador el rótulo basta; la longitud incorrecta es el error.

_ROTULO_RUC = (
    r"(?<![A-ZÑ])(?:R[.]?U[.]?C[.]?|REGISTRO UNICO DE CONTRIBUYENTES?)"
    r"\s*(?:(?:N[O°]?|NUMERO|NRO[.]?)\s*)?(?:[:,.]\s*)?(?<!\d)"
)
# [NEEDS CLARIFICATION] prefijos válidos del RUC; por defecto 10/15/16/17/20.
RE_RUC_DOC = re.compile(_ROTULO_RUC + r"((?:10|15|16|17|20)\d{9})(?!\d)")
RE_RUC_BORRADOR = re.compile(_ROTULO_RUC + r"(\d{9,13})(?!\d)")
# F22: como el DNI de F19, en el borrador el rótulo basta.

RE_PARTIDA = re.compile(
    r"(?<![A-ZÑ])(?:PARTIDA\s*(?:ELECTRONICA|REGISTRAL)?|FICHA\s*(?:REGISTRAL)?)"
    r"\s*N[O°]?\.?\s*(\d{5,})"
)
# La forma corta PARTIDA N° también es valida en algunos actos.
# F30: la FICHA (sistema anterior a la partida electrónica) es el mismo dato.

RE_MONTO = re.compile(
    r"(US\$|S/\.?|\$|(?<![A-ZÑ])(?:SOLES|DOLARES(?: AMERICANOS)?))\s*(\d[\d,]*\.\d{2})"
    r"|(\d[\d,]*\.\d{2})\s*(US\$|SOLES|DOLARES(?: AMERICANOS)?)"
)
# F27: moneda antes o después de la cifra. [NEEDS CLARIFICATION] "$" = dólares.


def _monto(m: re.Match) -> str:
    """Valor comparable: los soles solo con la cifra (formato previo), el resto US$."""
    moneda, importe = m.group(1) or m.group(4), m.group(2) or m.group(3)
    return importe if moneda.startswith("S") else f"US$ {importe}"


def montos_de(t: str) -> list[str]:
    return [_monto(m) for m in RE_MONTO.finditer(t)]


_CONCEPTOS = (
    ("PRECIO", r"PRECIO(?: DE (?:VENTA|LA COMPRAVENTA|COMPRA))?"),
    ("TASACION", r"(?:VALOR DE )?TASACION|VALOR TASADO"),
    ("VALOR_COMERCIAL", r"VALOR COMERCIAL"),
    ("VALOR_REALIZACION", r"VALOR DE REALIZACION"),
    ("HIPOTECA", r"HIPOTECA|GRAVAMEN"),
)
_CUALQUIER_CONCEPTO = "|".join(patron for _, patron in _CONCEPTOS)
RE_CANTIDAD = re.compile(
    r"(?<![A-ZÑ])(?:"
    + "|".join(f"(?P<{c}>{p})" for c, p in _CONCEPTOS)
    + r")(?![A-ZÑ])"
    rf"(?:(?!(?<!S/)\.\s|(?<![A-ZÑ])(?:{_CUALQUIER_CONCEPTO})(?![A-ZÑ])).){{0,160}}?"
    r"(?<![\d,.])(?P<cifra>\d{1,3}(?:,\d{3})+\.\d{2}|\d+\.\d{2})(?!\d)"
)
# F30: la primera cifra con dos decimales tras el concepto, en la misma oración y
# antes de otro concepto; con o sin moneda. Un punto tras abreviatura corta la
# oración: se pierde la cantidad, no hay falso positivo.


def cantidades_de(t: str) -> list[tuple[str, str]]:
    """F30: (concepto, cifra) de cada precio, tasación, valor o hipoteca."""
    return [
        (next(c for c, _ in _CONCEPTOS if m[c]), m["cifra"])
        for m in RE_CANTIDAD.finditer(t)
    ]


_ZONAS_REGISTRALES = (
    "PIURA CHICLAYO MOYOBAMBA IQUITOS TRUJILLO PUCALLPA HUARAZ HUANCAYO LIMA CUSCO "
    "ICA AREQUIPA TACNA AYACUCHO"
).split()
# Sede de cada zona registral de SUNARP, de la I a la XIV.
_ROMANOS = {
    d + u: 10 * i + j
    for i, d in enumerate(("", "X", "XX", "XXX"))
    for j, u in enumerate(("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"))
    if i or j
}
_PARADAS_LUGAR = {
    *"A AL CON DE DEL EL EN LA LAS LOS N NO QUE SE Y".split(),
    *"ASIENTO BAJO DEPARTAMENTO DISTRITO FICHA PARTIDA PROVINCIA SEDE ZONA".split(),
}
_REGISTROS = (
    "PREDIOS|PROPIEDAD INMUEBLE|PROPIEDAD VEHICULAR|PERSONAS JURIDICAS|"
    "PERSONAS NATURALES|SOCIEDADES|MANDATOS Y PODERES|BIENES MUEBLES|TESTAMENTOS|"
    "SUCESIONES INTESTADAS"
)
_DATOS_REGISTRALES = (
    (
        "ZONA",
        re.compile(
            r"(?<![A-ZÑ])ZONA REGISTRAL\s*(?:N[O°]?\.?\s*)?([IVX]+)(?![A-ZÑ])"
            r"(?:\s*[-–,]?\s*SEDE\s+([A-ZÑ]+))?"
        ),
    ),
    (
        "REGISTRO",
        re.compile(rf"(?<![A-ZÑ])REGISTRO (?:DE (?:LA )?)?({_REGISTROS})(?![A-ZÑ])"),
    ),
    (
        "OFICINA",
        re.compile(
            r"(?<![A-ZÑ])OFICINA REGISTRAL\s*(?:DE |DEL )?([A-ZÑ]+(?: [A-ZÑ]+){0,2})"
        ),
    ),
    (
        "PROVINCIA",
        re.compile(
            r"(?<![A-ZÑ])PROVINCIA(?: Y DEPARTAMENTO)?\s*(?:DE |:\s*)([A-ZÑ]+(?: [A-ZÑ]+){0,2})"
        ),
    ),
)
# F30 [NEEDS CLARIFICATION] «provincia» se lee como el lugar tras PROVINCIA DE;
# también puede ser la provincia de la oficina registral, que va en OFICINA.


def datos_registrales(t: str) -> list[tuple[str, str, re.Match]]:
    """F30: (clase, valor, match) de cada zona, registro, oficina y provincia.

    Un lugar (oficina, provincia) termina en la primera palabra de ``_PARADAS_LUGAR``.
    """
    datos = []
    for clase, patron in _DATOS_REGISTRALES:
        for m in patron.finditer(t):
            palabras = m[1].split()
            corte = len(palabras)
            if clase in {"OFICINA", "PROVINCIA"}:
                corte = next(
                    (
                        i
                        for i, w in enumerate(palabras)
                        if w in _PARADAS_LUGAR
                        and not (i == 0 and w in {"EL", "LA", "LOS", "LAS"})
                    ),
                    corte,
                )
            if valor := " ".join(palabras[:corte]):
                datos.append((clase, valor, m))
    return datos


RE_NOMBRE = re.compile(
    r"([A-ZÑ][A-ZÑ ]{8,60}?)[,.]{0,2}-?\s*(?:DE\s+)?NACIONALIDAD"
    r"|CASAD[AO]\s+CON\s+([A-ZÑ][A-ZÑ ]{8,60}?)[,.]"
)
# Nombre en mayusculas antes de NACIONALIDAD o despues de CASAD@ CON.
RE_NOMBRE_APELLIDOS = re.compile(
    r"([A-ZÑ][A-ZÑ ]{2,60}),\s*([A-ZÑ][A-ZÑ ]{2,60})"
    r"\s+(?:DE\s+)?NACIONALIDAD"
)

RE_RENIEC = {"nom": "NOMBRES", "pat": "APELLIDO PATERNO", "mat": "APELLIDO MATERNO"}
# Valor de «Sexo» o «Estado civil» que quedó suelto cuando la marca de agua tapó
# su rótulo: nunca es nombre ni apellido.
_VALORES_NO_NOMBRE = re.compile(r"(?:FEMENIN|MASCULIN|SOLTER|CASAD|VIUD|DIVORCIAD)[AO]")
# Rótulo ``Texto:`` al inicio de línea; su valor nunca es el de otro rótulo (F18).
_ROTULO = re.compile(r"[A-Za-zÁÉÍÓÚÑáéíóúñ .]{3,40}:")


def _primera_celda_siguiente(lineas: list[str], indice: int) -> str:
    """Valor que el escaneo bajó a la línea siguiente, si no es otro rótulo."""
    if indice + 1 == len(lineas) or _ROTULO.match(
        siguiente := lineas[indice + 1].strip()
    ):
        return ""
    return re.split(r"\s{2,}", siguiente)[0]


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
    lineas = raw.splitlines()
    for j, linea in enumerate(lineas):
        celdas = [norm(x).rstrip(":") for x in re.split(r"\s{2,}", linea)]
        for i, cel in enumerate(celdas):
            for k, etq in RE_RENIEC.items():
                if cel != etq:
                    continue
                valor = celdas[i + 1] if i + 1 < len(celdas) else ""
                if not valor.replace(" ", "").isalpha():
                    valor = norm(_primera_celda_siguiente(lineas, j))
                if valor.replace(" ", "").isalpha() and not (
                    _VALORES_NO_NOMBRE.fullmatch(valor)
                ):
                    c.setdefault(k, valor)
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


def _celdas(linea: str) -> list[str]:
    """Conserva la frontera de columnas que ``ocr_lineas`` marca con dos espacios."""
    celdas = []
    for celda in re.split(r"\s{2,}", linea):
        valor = norm(celda)
        if valor:
            celdas.append(valor)
    return celdas


def _linea_etiquetada(raw: str, etiqueta: str) -> str | None:
    """Lee campos de formularios sin interpretar números cercanos."""
    for linea in raw.splitlines():
        celdas = _celdas(linea)
        for indice, celda in enumerate(celdas):
            rotulo = re.sub(r"^\d+[.)]?\s*", "", celda).rstrip(":")
            if rotulo.startswith(f"{etiqueta}:"):
                return rotulo[len(etiqueta) + 1 :].lstrip()
            if rotulo != etiqueta or indice + 1 == len(celdas):
                continue
            resto = celdas[indice + 1]
            if etiqueta == "NOMBRES" and resto.startswith(("Y ", "DEL ")):
                continue
            return resto
        t = re.sub(r"^\d+[.)]?\s*", "", norm(linea))
        if not t.startswith(etiqueta):
            continue
        resto = t[len(etiqueta) :].lstrip(" :")
        if etiqueta == "NOMBRES" and resto.startswith(("Y ", "DEL ")):
            continue
        if resto:
            return resto
    return None


def _campo_reniec(raw: str, etiqueta: str) -> str | None:
    """Lee solo un rótulo al inicio de línea y su propia celda.

    Sin valor en la celda, lo toma de la línea siguiente (F18); una dirección
    así leída debe tener alguna palabra y un dígito o una abreviatura de vía:
    un número suelto es un fragmento, no una dirección.
    """
    lineas = raw.splitlines()
    for indice, linea in enumerate(lineas):
        celdas = re.split(r"\s{2,}", linea.strip())
        primera = celdas[0]
        rotulo, _, valor = primera.partition(":")
        if norm(rotulo) != etiqueta:
            continue
        valor = valor.strip() or (celdas[1].strip() if len(celdas) > 1 else "")
        if not valor:
            valor = _primera_celda_siguiente(lineas, indice)
            palabras = set(re.findall(r"[A-ZÑ]+", norm(valor)))
            if etiqueta == "DIRECCION" and not (
                palabras and (re.search(r"\d", valor) or _VIAS.keys() & palabras)
            ):
                valor = ""
        return valor or None
    return None


def _fecha_reniec(valor: str | None) -> date | None:
    # El OCR mete puntos o espacios entre dígitos: 12/05/1.978, 12/05/1 978.
    valor = valor and re.sub(r"(?<=\d)[.\s](?=\d)", "", valor)
    if not valor or not (
        coincide := re.fullmatch(r"([0-9]{2})([/\-])([0-9]{2})\2([0-9]{4})", valor)
    ):
        return None
    try:
        return date(int(coincide[4]), int(coincide[3]), int(coincide[1]))
    except ValueError:
        return None


def _campos_reniec(pagina: Pagina) -> dict:
    raw = pagina.texto
    civil = _campo_reniec(raw, "ESTADO CIVIL")
    civil = {
        "SOLTERA": "SOLTERO",
        "SOLTERO": "SOLTERO",
        "CASADA": "CASADO",
        "CASADO": "CASADO",
        "VIUDA": "VIUDO",
        "VIUDO": "VIUDO",
        "DIVORCIADA": "DIVORCIADO",
        "DIVORCIADO": "DIVORCIADO",
    }.get(norm(civil).rstrip(".") if civil else "")
    fecha = _fecha_reniec(_campo_reniec(raw, "FECHA DE NACIMIENTO"))
    emision = _fecha_reniec(_campo_reniec(raw, "FECHA DE EMISION"))
    valores = {
        "estado_civil": civil,
        "fecha_nacimiento": fecha,
        "domicilio": _campo_reniec(raw, "DIRECCION"),
        "distrito": _campo_reniec(raw, "DISTRITO DE DOMICILIO"),
    }
    origen = Procedencia(pagina.fuente, pagina.numero)
    return {
        **valores,
        **{
            f"procedencia_{campo}": origen if valor is not None else None
            for campo, valor in valores.items()
        },
        "fecha_emision": emision,
        "emisiones_campos": tuple(
            emision if valor is not None else None for valor in valores.values()
        ),
    }


def _anotar_reniec(personas: list[Persona], pagina: Pagina, tipo: str) -> list[Persona]:
    if (
        tipo == "RENIEC"
        and len(personas) == 1
        and personas[0].nombre
        and personas[0].documento
    ):
        return [personas[0]._replace(**_campos_reniec(pagina))]
    return personas


def _nombres_de_pagina(
    raw: str, tipo: str, es_pdf: bool, es_img: bool = False
) -> list[str]:
    t = norm(raw)
    out = list(nombres(t))
    # Solo la coma delimita el orden ``APELLIDOS, NOMBRES``; no se reordena
    # ninguna línea de prosa que no tenga esa frontera explícita.
    if tipo in {"RENIEC", "BIOMETRICA", "SUNARP", "IDENTIDAD", "PROSA"}:
        out.extend(
            f"{nombres_propios.strip().removesuffix(' DE')} {apellidos.strip()}"
            for apellidos, nombres_propios in RE_NOMBRE_APELLIDOS.findall(t)
        )
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
    """Registros de la página; el cónyuge de la declaración jurada no es uno."""
    conyuge = (
        _linea_etiquetada(pagina.texto, "NOMBRES Y APELLIDOS DEL CONYUGE")
        if tipo == "DECLARACION_JURADA"
        else None
    )
    personas = _registros_de_pagina(pagina, tipo, _nombre_clave(conyuge))
    if not conyuge:
        return personas
    origen = Procedencia(pagina.fuente, pagina.numero)
    declarantes = [indice for indice, p in enumerate(personas) if p.nombre]
    if len(declarantes) == 1:
        personas[declarantes[0]] = personas[declarantes[0]]._replace(
            conyuge=conyuge, procedencia_conyuge=origen
        )
    else:
        personas.append(
            Persona(
                None,
                None,
                (origen,),
                "SIN_FICHA",
                conyuge=conyuge,
                procedencia_conyuge=origen,
            )
        )
    return personas


def _registros_de_pagina(pagina: Pagina, tipo: str, excluido: str) -> list[Persona]:
    sufijo = _sufijo(pagina.fuente.rsplit("/", 1)[-1])
    es_img = bool(sufijo and sufijo in IMGS)
    procedencia = (Procedencia(pagina.fuente, pagina.numero),)

    def nombres_sin_excluido(raw):
        return [
            nombre
            for nombre in _nombres_de_pagina(raw, tipo, sufijo == ".pdf", es_img)
            if not excluido or _nombre_clave(nombre) != excluido
        ]

    # Una línea con nombre y documento es una frontera verificable. La usamos
    # primero para no cruzar a dos comparecientes de la misma página; los
    # formularios RENIEC/biométricos caen al bloque completo porque sus campos
    # viven en líneas distintas.
    asociados = []
    for linea in pagina.texto.splitlines():
        nombres_linea = nombres_sin_excluido(linea)
        documentos_linea = _documentos_de_pagina(linea, tipo, es_img)
        if len(nombres_linea) == 1 and len(documentos_linea) == 1:
            asociados.append(
                Persona(nombres_linea[0], documentos_linea[0], procedencia)
            )
    if asociados:
        return _anotar_reniec(asociados, pagina, tipo)
    nombres_pagina = nombres_sin_excluido(pagina.texto)
    documentos = _documentos_de_pagina(pagina.texto, tipo, es_img)
    if len(nombres_pagina) == 1 and len(documentos) == 1:
        return _anotar_reniec(
            [Persona(nombres_pagina[0], documentos[0], procedencia)], pagina, tipo
        )
    personas = [
        Persona(nombre, None, procedencia, "SIN_DOCUMENTO") for nombre in nombres_pagina
    ]
    personas.extend(
        Persona(None, documento, procedencia, "REVISION_MANUAL")
        for documento in documentos
    )
    return personas


def _nombre_clave(nombre: str | None) -> str:
    """Normaliza solo nombres explícitos; no aproxima ni reordena prosa."""
    if not nombre:
        return ""
    limpio = norm(nombre)
    if "," in limpio:
        apellidos, nombres_propios = (parte.strip() for parte in limpio.split(",", 1))
        limpio = f"{nombres_propios} {apellidos}"
    return re.sub(r"[^A-ZÑ ]", " ", limpio).strip()


def _nombre_dudoso(uno: str, otro: str) -> bool:
    """Más de 2 ediciones o nombre truncado, sobre la clave sin espacios (F15)."""
    uno, otro = (_nombre_clave(n).replace(" ", "") for n in (uno, otro))
    corta, larga = sorted((uno, otro), key=len)
    return Levenshtein.distance(uno, otro) > 2 or (
        len(corta) < len(larga) and corta in larga
    )


def _rango_ficha(persona: Persona, tipo: str) -> tuple:
    """Menor manda: RENIEC, luego emisión más reciente; empate, orden de página."""
    fecha = persona.fecha_emision
    return (tipo != "RENIEC", fecha is None, -fecha.toordinal() if fecha else 0)


def unificar_personas(personas, tipos=None) -> tuple[Persona, ...]:
    """Unifica únicamente evidencia fuerte y conserva todo lo ambiguo.

    El criterio deliberadamente pierde unificaciones legítimas antes que
    atribuir un documento a otra persona: documento exacto más nombre exacto
    (admitiendo ``APELLIDOS, NOMBRES``), o nombre exacto cuando ambos bloques
    carecen de documento. Nombres parecidos nunca son una identidad.

    Con ``tipos`` (anclas de ``catalogo()``, F15) el documento exacto basta:
    manda el nombre de la mejor ficha y la variante queda como adjunto.
    """
    unificadas: list[Persona] = []
    rangos = []
    for posicion, persona in enumerate(personas):
        clave_nombre = _nombre_clave(persona.nombre)
        rango = _rango_ficha(persona, tipos[posicion]) if tipos else None
        fusion = None
        for indice, existente in enumerate(unificadas):
            if (
                persona.conyuge
                and existente.conyuge
                and _nombre_clave(persona.conyuge) != _nombre_clave(existente.conyuge)
            ):
                continue
            mismo_documento = (
                persona.documento
                and existente.documento
                and persona.documento == existente.documento
            )
            ambos_sin_documento = (
                not persona.documento
                and not existente.documento
                and clave_nombre
                and clave_nombre == _nombre_clave(existente.nombre)
            )
            if mismo_documento and (
                tipos or clave_nombre == _nombre_clave(existente.nombre)
            ):
                fusion = indice
                break
            if ambos_sin_documento:
                fusion = indice
                break
        if fusion is None:
            unificadas.append(persona)
            rangos.append(rango)
            continue
        existente = unificadas[fusion]
        nombre = existente.nombre or persona.nombre
        adjuntos = existente.adjuntos
        nombre_dudoso = False
        if tipos and clave_nombre != _nombre_clave(existente.nombre):
            ganadora, variante = (
                (persona, existente) if rango < rangos[fusion] else (existente, persona)
            )
            ajenas = {p for a in adjuntos or () for p in a.procedencias}
            nombre = ganadora.nombre
            adjuntos = (
                *(adjuntos or ()),
                Persona(
                    variante.nombre,
                    variante.documento,
                    tuple(p for p in variante.procedencias if p not in ajenas),
                ),
            )
            nombre_dudoso = _nombre_dudoso(ganadora.nombre, variante.nombre)
        if tipos:
            rangos[fusion] = min(rango, rangos[fusion])
        procedencias = tuple(
            dict.fromkeys((*existente.procedencias, *persona.procedencias))
        )
        estado = (
            "CONFIRMADA"
            if existente.documento or persona.documento
            else "SIN_DOCUMENTO"
        )
        campos = {}
        nombres_campos = ("estado_civil", "fecha_nacimiento", "domicilio", "distrito")
        emisiones = []
        conflicto = False
        for posicion, campo in enumerate(nombres_campos):
            anterior = getattr(existente, campo)
            nuevo = getattr(persona, campo)
            fecha_anterior = (
                existente.emisiones_campos or (existente.fecha_emision,) * 4
            )[posicion]
            fecha_nueva = (persona.emisiones_campos or (persona.fecha_emision,) * 4)[
                posicion
            ]
            conflicto |= (
                anterior is not None and nuevo is not None and anterior != nuevo
            )
            usar_nueva = anterior is None or (
                nuevo is not None
                and fecha_nueva is not None
                and (fecha_anterior is None or fecha_nueva > fecha_anterior)
            )
            elegida = persona if usar_nueva else existente
            campos[campo] = getattr(elegida, campo)
            campos[f"procedencia_{campo}"] = getattr(elegida, f"procedencia_{campo}")
            emisiones.append(fecha_nueva if usar_nueva else fecha_anterior)
        unificadas[fusion] = existente._replace(
            nombre=nombre,
            documento=existente.documento or persona.documento,
            procedencias=procedencias,
            adjuntos=adjuntos,
            conyuge=existente.conyuge or persona.conyuge,
            procedencia_conyuge=existente.procedencia_conyuge
            or persona.procedencia_conyuge,
            estado="REVISION_MANUAL"
            if conflicto
            or nombre_dudoso
            or "REVISION_MANUAL" in (existente.estado, persona.estado)
            else estado,
            fecha_emision=max(
                (
                    fecha
                    for fecha in (existente.fecha_emision, persona.fecha_emision)
                    if fecha
                ),
                default=None,
            ),
            emisiones_campos=tuple(emisiones) if any(emisiones) else None,
            **campos,
        )
    documentos = {}
    for persona in unificadas:
        if persona.documento and persona.nombre:
            documentos.setdefault(persona.documento, set()).add(
                _nombre_clave(persona.nombre)
            )
    return tuple(
        persona._replace(
            estado="REVISION_MANUAL"
            if persona.documento and len(documentos.get(persona.documento, ())) > 1
            else persona.estado,
        )
        for persona in unificadas
    )


def _catalogo_borrador(borrador) -> Catalogo:
    if isinstance(borrador, Catalogo):
        return borrador
    if isinstance(borrador, str):
        return catalogo({"borrador": borrador})
    raise TypeError("borrador debe ser texto o Catalogo")


def comparar_personas(fuente: Catalogo, borrador) -> tuple[dict, ...]:
    """Compara titulares de documentos sin alterar las reglas históricas."""
    if not isinstance(fuente, Catalogo):
        raise TypeError("fuente debe ser Catalogo")
    destino = _catalogo_borrador(borrador)
    # Titular = ancla; pertenencia del documento = cualquier fuente (research D8).
    por_nombre = {}
    for persona in fuente.personas:
        if persona.nombre:
            por_nombre.setdefault(_nombre_clave(persona.nombre), []).append(persona)
    documentos = fuente["DNI"]

    observaciones = []
    vistos = set()
    for persona in destino._registros():
        if not persona.documento:
            continue
        nombre_clave = _nombre_clave(persona.nombre)
        titulares = por_nombre.get(nombre_clave, []) if nombre_clave else []
        titular = titulares[0] if len(titulares) == 1 else None
        esperado = titular.documento if titular else None
        if (
            titular
            and esperado
            and esperado != persona.documento
            and persona.documento in documentos
        ):
            observacion = {
                "tipo": "DOCUMENTO_CRUZADO",
                "nombre": persona.nombre,
                "documento_hallado": persona.documento,
                "documento_esperado": esperado,
                "procedencias": titular.procedencias,
            }
        elif persona.documento not in documentos:
            observacion = {
                "tipo": "DOCUMENTO_SIN_TITULAR",
                "nombre": persona.nombre,
                "documento_hallado": persona.documento,
                "documento_esperado": None,
                "procedencias": (),
            }
        else:
            continue
        clave = (
            observacion["tipo"],
            observacion["nombre"],
            observacion["documento_hallado"],
            observacion["documento_esperado"],
        )
        if clave not in vistos:
            observaciones.append(observacion)
            vistos.add(clave)
    return tuple(observaciones)


_REPRESENTACION = re.compile(
    r"(?<![A-ZÑ])(?:REPRESENTACION|REPRESENTANTE|APODERAD[AO])(?![A-ZÑ])"
)
_CIVIL_BORRADOR = re.compile(
    r"\b(CASAD[AO]\s+CON|SOLTER[AO]|VIUD[AO]|DIVORCIAD[AO]|CONVIVIENTE)\b"
)
_VIAS = {
    "AV": "AVENIDA",
    "JR": "JIRON",
    "CA": "CALLE",
    "PSJ": "PASAJE",
    "MZ": "MANZANA",
    "LT": "LOTE",
    "URB": "URBANIZACION",
    "AAHH": "ASENTAMIENTO HUMANO",
    "ASENT": "ASENTAMIENTO",
    "ASOC": "ASOCIACION",
    "DPTO": "DEPARTAMENTO",
    "INT": "INTERIOR",
    "N": "NUMERO",
    "Nº": "NUMERO",
    "N°": "NUMERO",
    "SN": "SIN NUMERO",
}


def _clausula_persona(texto: str, nombre: str, documento: str) -> str | None:
    lineas = [norm(linea) for linea in texto.splitlines()]
    t = "\n".join(lineas)
    nombre_exacto = rf"(?<![A-ZÑ]){re.escape(_nombre_clave(nombre))}(?![A-ZÑ])"
    dni = rf"(?<!\d){re.escape(documento)}(?!\d)"
    # La carátula repite el nombre: primero la línea de comparecencia.
    for patron, con_civil in ((dni, True), (nombre_exacto, True), (dni, False)):
        for linea in lineas:
            if re.search(patron, linea) and (
                not con_civil or _CIVIL_BORRADOR.search(linea)
            ):
                return linea
    match = re.search(nombre_exacto, t)
    if not match:
        return None
    limites = list(re.finditer(r"\.\s+|\n", t[: match.start()]))
    inicio = limites[-1].end() if limites else 0
    if not t[inicio : match.start()].strip() and limites:
        inicio = limites[-2].end() if len(limites) > 1 else 0
    fin = re.search(r"\.\s+|\n", t[match.end() :])
    return t[inicio : match.end() + fin.start() if fin else len(t)]


def _direccion_palabras(texto: str) -> list[str]:
    sin_tildes = "".join(
        c
        for c in unicodedata.normalize("NFKD", texto.upper())
        if not unicodedata.combining(c)
    )
    sin_tildes = re.sub(r"\bS\s*/\s*N\b", " SN ", sin_tildes)
    sin_tildes = re.sub(r"N[°º]", " N ", sin_tildes).replace("#", " INTERIOR ")
    # RENIEC abrevia «ASENT.H.» y «AA.HH.», y pega el número: «LT6», «MZ.44».
    sin_tildes = re.sub(r"\b(?:ASENT\.?\s*H|AA\.?\s*HH)\b\.?", " AAHH ", sin_tildes)
    sin_tildes = re.sub(r"\b(MZ|LT|DPTO|INT)(?=\d)", r"\1 ", sin_tildes)
    tokens = re.findall(r"[A-Z0-9]+", sin_tildes)
    # «LOTE 05» y «LT.5» son el mismo número.
    tokens = [t.lstrip("0") or "0" if t.isdigit() else t for t in tokens]
    return [palabra for token in tokens for palabra in _VIAS.get(token, token).split()]


def _direccion_tokens(texto: str) -> Counter:
    return Counter(_direccion_palabras(texto))


_ROTULO_DIRECCION_FUENTE = re.compile(
    r"(?<![A-ZÑ])(?<!DE )(?:CON DOMICILIO(?: LEGAL| FISCAL)? EN|DOMICILIAD[AO] EN"
    r"|DOMICILIO(?: LEGAL| FISCAL)?(?: EN)?|DIRECCION"
    r"|UBICAD[AO] EN|SIT[AO] EN|UBICACION(?: DEL PREDIO| DEL INMUEBLE)?)(?![A-ZÑ])[\s:|]*"
)
# «DISTRITO DE DOMICILIO» y similares rotulan otra cosa: de ahí el (?<!DE ).
_ROTULO_DIRECCION_BORRADOR = re.compile(
    r"(?<![A-ZÑ])(?:CON DOMICILIO|DOMICILIAD[AO]|DOMICILIO LEGAL|UBICAD[AO]|SIT[AO])"
    r" EN(?![A-ZÑ])[\s:]*"
)
# F30: «UBICADO EN» y «SITO EN» rotulan la dirección del bien.
_PALABRAS_VIA = {via.split()[0] for via in _VIAS.values()} - {"NUMERO", "SIN"}


def _direcciones(texto: str, rotulo: re.Pattern) -> list[str]:
    """F22: tramos tras el rótulo hasta el fin de cláusula, línea por línea."""
    out = []
    for linea in texto.splitlines():
        # Dos espacios separan celdas (``ocr_lineas``): una celda cierra el tramo.
        t = norm(" | ".join(re.split(r"\s{2,}", linea.strip())))
        for m in rotulo.finditer(t):
            tramo = re.split(
                r"\||;|,\s*(?:DISTRITO|PROVINCIA|DEPARTAMENTO)\b", t[m.end() :]
            )[0]
            # ponytail: un punto tras palabra de hasta 4 letras es abreviatura
            # (AV., JR., MZ.); si una vía corta cierra la cláusula, se arrastra texto
            # y la similitud baja: se pierde la observación, no hay falso positivo.
            for punto in re.finditer(r"([A-ZÑ0-9]*)\.(?=\s|$)", tramo):
                if not (punto[1].isalpha() and len(punto[1]) <= 4):
                    tramo = tramo[: punto.end() - 1]
                    break
            if tramo := tramo.strip(" ,."):
                out.append(tramo)
    return out


def _palabras_clave(texto: str) -> list[str]:
    # El «N°» delante del número es opcional en la escritura.
    return [w for w in _direccion_palabras(texto) if w not in {"NUMERO", "NO", "NRO"}]


def _clave_direccion(texto: str) -> str:
    return " ".join(_palabras_clave(texto))


def _sustitucion(fuente: Counter, tramo: Counter, vocabulario) -> bool | None:
    """F22 ronda 2: None si es otra dirección; si no, ¿hay una sustitución real?

    El borrador puede agregar (interior, distrito, referencia); solo cuenta lo
    que falta de la fuente y trae pareja en el borrador.
    """
    faltan = fuente - tramo
    sobran = tramo - fuente
    if sum(faltan.values()) > sum((fuente & tramo).values()):
        return None
    real = False
    for w in sorted(faltan.elements()):
        candidatas = sorted(v for v in sobran if v.isdigit() == w.isdigit())
        if w.isdigit():
            if not candidatas:
                return None
            pareja, real = candidatas[0], True
        else:
            pareja = min(
                candidatas, key=lambda v: Levenshtein.distance(w, v), default=None
            )
            if len(w) < 4 or pareja is None or Levenshtein.distance(w, pareja) > 2:
                return None
            # [NEEDS CLARIFICATION] sin diccionario en el núcleo: la palabra de la
            # fuente vale si se lee dos veces y la del borrador no está en fuentes.
            real = real or (
                vocabulario[pareja] == 0 and (vocabulario[w] >= 2 or w in _PALABRAS_VIA)
            )
        sobran[pareja] -= 1
        sobran = +sobran
    return real


def _direcciones_observadas(
    fuente, borrador: str, vocabulario
) -> list[tuple[str, str]]:
    """F22: (hallado, esperado) por cada mención con una sustitución real."""
    claves = {}
    for direccion in sorted(fuente):
        claves.setdefault(_clave_direccion(direccion), direccion)
    claves.pop("", None)
    cuentas = {c: Counter(c.split()) for c in claves}
    obs = []
    for tramo in _direcciones(borrador, _ROTULO_DIRECCION_BORRADOR):
        palabras = Counter(_palabras_clave(tramo))
        if any(c <= palabras for c in cuentas.values()):
            continue
        for clave, cuenta in cuentas.items():
            if _sustitucion(cuenta, palabras, vocabulario):
                obs.append((tramo, claves[clave]))
                break
    return obs


def revisar_persona_ampliada(
    cat: Catalogo, borrador: str, hoy: date | None = None
) -> tuple[dict, ...]:
    """Observaciones F12 puras: la fecha de referencia siempre llega del llamador."""
    observaciones = []
    # F22: la aparición errónea ya sale como [DIRECCION] en revisar().
    observadas = {
        _clave_direccion(esperado)
        for _, esperado in _direcciones_observadas(
            cat["DIRECCION"], borrador, cat.vocabulario
        )
    }
    # Un representante declara el domicilio de su representada: se coteja con
    # las direcciones de los recaudos, no con los domicilios RENIEC personales.
    personales = {norm(p.domicilio) for p in cat._registros() if p.domicilio}
    recaudos = [_direccion_tokens(d) for d in cat.direcciones - personales]
    for persona in cat.personas:
        if (
            persona.estado != "CONFIRMADA"
            or not persona.documento
            or not persona.nombre
        ):
            continue
        clausula = _clausula_persona(borrador, persona.nombre, persona.documento)
        if clausula is None:
            continue
        base = {"nombre": persona.nombre}
        if persona.estado_civil:
            marcadores = _CIVIL_BORRADOR.findall(clausula)
            hallado = marcadores[0] if marcadores else "Sin marcador de estado civil"
            if persona.estado_civil == "CASADO" and (
                not marcadores or any(m.startswith("SOLTER") for m in marcadores)
            ):
                tipo = (
                    "ESTADO_CIVIL_DISCREPANTE"
                    if marcadores
                    else "CONYUGE_NO_MENCIONADO"
                )
            elif persona.estado_civil == "SOLTERO" and any(
                m.startswith("CASAD") for m in marcadores
            ):
                tipo = "ESTADO_CIVIL_DISCREPANTE"
            else:
                tipo = None
            if tipo:
                observaciones.append(
                    {
                        **base,
                        "tipo": tipo,
                        "esperado": persona.estado_civil,
                        "hallado": hallado,
                        "procedencia": persona.procedencia_estado_civil,
                    }
                )
        if persona.fecha_nacimiento and hoy is not None:
            edad = (
                hoy.year
                - persona.fecha_nacimiento.year
                - (
                    (hoy.month, hoy.day)
                    < (persona.fecha_nacimiento.month, persona.fecha_nacimiento.day)
                )
            )
            if 0 <= edad < 18:
                observaciones.append(
                    {
                        **base,
                        "tipo": "MENOR_DE_EDAD",
                        "edad": edad,
                        "fecha_referencia": hoy,
                        "esperado": persona.fecha_nacimiento,
                        "hallado": "Menor de edad",
                        "procedencia": persona.procedencia_fecha_nacimiento,
                    }
                )
        if persona.domicilio:
            direccion = _direccion_tokens(persona.domicilio)
            # ponytail: busca en la línea del compareciente; ampliar al párrafo si hay domicilios multilínea.
            # F16: cualquier línea con su nombre exacto o su DNI exacto.
            dni = re.compile(rf"(?<!\d){re.escape(persona.documento)}(?!\d)")
            oraciones = [
                linea
                for linea in borrador.splitlines()
                if _nombre_clave(persona.nombre) in norm(linea) or dni.search(linea)
            ]
            representada = any(
                _REPRESENTACION.search(norm(oracion))
                and any(d <= _direccion_tokens(oracion) for d in recaudos if d)
                for oracion in oraciones
            )
            if (
                not representada
                and not any(
                    direccion <= _direccion_tokens(oracion) for oracion in oraciones
                )
                and (_clave_direccion(persona.domicilio) not in observadas)
            ):
                observaciones.append(
                    {
                        **base,
                        "tipo": "DOMICILIO_NO_ENCONTRADO",
                        "esperado": persona.domicilio,
                        "hallado": "No aparece en el borrador",
                        "procedencia": persona.procedencia_domicilio,
                    }
                )
    return tuple(observaciones)


def _paginas(fuentes: Mapping[str, str]) -> list[Pagina]:
    return [
        Pagina(nombre, numero, texto)
        for nombre, raw in fuentes.items()
        for numero, texto in enumerate(raw.split(SEPARADOR_PAGINA), 1)
    ]


_TIPOS_ANCLA = {"RENIEC", "BIOMETRICA"}


def _pegar(anclas, registros) -> tuple[tuple[Persona, ...], tuple[Persona, ...]]:
    """Adjunta cada registro no oficial a un ancla única o lo deja como mención.

    Documento exacto o, sin documento, clave de nombre exacta. Un registro con
    documento ajeno a las anclas nunca se pega por nombre (research D4).
    """
    anclas = list(anclas)
    adjuntos = [[] for _ in anclas]
    menciones = []
    for registro in registros:
        clave = _nombre_clave(registro.nombre)
        indices = [
            indice
            for indice, ancla in enumerate(anclas)
            if (
                ancla.documento == registro.documento
                if registro.documento
                else clave
                and any(
                    _nombre_clave(propio.nombre) == clave
                    for propio in (ancla, *(ancla.adjuntos or ()))
                )
            )
        ]
        if len(indices) != 1:
            menciones.append(registro)
            continue
        indice = indices[0]
        adjuntos[indice].append(registro)
        if registro.conyuge and not anclas[indice].conyuge:
            anclas[indice] = anclas[indice]._replace(
                conyuge=registro.conyuge,
                procedencia_conyuge=registro.procedencia_conyuge,
            )
    return (
        tuple(
            ancla._replace(adjuntos=(*(ancla.adjuntos or ()), *propios) or None)
            for ancla, propios in zip(anclas, adjuntos)
        ),
        tuple(
            mencion._replace(estado="SIN_FICHA")
            for mencion in unificar_personas(menciones)
        ),
    )


def catalogo(fuentes: Mapping[str, str]) -> Catalogo:
    anclas = []
    tipos = []
    resto = []
    partidas = set()
    montos = set()
    rucs = set()
    direcciones = set()
    vocabulario = Counter()
    cantidades = set()
    registrales = set()
    descartadas = []
    no_clasificadas = []
    sueltas = {}
    for pagina in _paginas(fuentes):
        t = norm(pagina.texto)
        partidas.update(RE_PARTIDA.findall(t))
        montos.update(montos_de(t))
        tipo = clasificar_pagina(pagina.texto)
        if tipo in _TIPOS_DESCARTADOS:
            descartadas.append(PaginaDescartada(pagina.fuente, pagina.numero, tipo))
            continue
        rucs.update(RE_RUC_DOC.findall(t))
        cantidades.update(cantidades_de(t))
        registrales.update((clase, valor) for clase, valor, _ in datos_registrales(t))
        vocabulario.update(_direccion_palabras(t))
        direcciones.update(
            tramo
            for tramo in _direcciones(pagina.texto, _ROTULO_DIRECCION_FUENTE)
            if re.search(r"\d", tramo) or _PALABRAS_VIA & {*_direccion_palabras(tramo)}
        )
        personas_pagina = _personas_de_pagina(pagina, tipo)
        if tipo == "DESCONOCIDA" and personas_pagina:
            no_clasificadas.append(PaginaDescartada(pagina.fuente, pagina.numero, tipo))
        for persona in personas_pagina:
            if tipo in _TIPOS_ANCLA and persona.nombre and persona.documento:
                anclas.append(persona)
                tipos.append(tipo)
            else:
                resto.append(persona)
        # F18: RENIEC sin nombre legible; sus campos van al ancla de su DNI.
        if tipo == "RENIEC" and [p.nombre for p in personas_pagina] == [None]:
            sueltas[len(resto) - 1] = _campos_reniec(pagina)
    anclas = list(unificar_personas(anclas, tipos))
    por_documento = {ancla.documento: i for i, ancla in enumerate(anclas)}
    for indice, campos in sueltas.items():
        if (i := por_documento.get(resto[indice].documento)) is None:
            continue
        ficha = resto[indice]._replace(
            nombre=anclas[i].nombre, estado=anclas[i].estado, **campos
        )
        (anclas[i],) = unificar_personas((anclas[i], ficha))
        resto[indice] = None
    resto = [registro for registro in resto if registro]
    personas, menciones = _pegar(anclas, resto)
    return Catalogo(
        personas,
        frozenset(partidas),
        frozenset(montos),
        tuple(descartadas),
        tuple(no_clasificadas),
        menciones,
        rucs,
        direcciones,
        vocabulario,
        cantidades,
        registrales,
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


def nombres_exigibles(cat: Catalogo, textos) -> frozenset[str]:
    """Nombres de las anclas y de los textos dados (la minuta, según el llamador).

    F22: incluye los RUC de esos textos; un RUC nunca es un nombre.
    """
    propios = [catalogo({"exigible": texto}) for texto in textos]
    return frozenset(p.nombre for p in cat.personas) | {
        v for c in propios for v in c["NOMBRE"] | c["RUC"]
    }


def montos_exigibles(textos) -> frozenset[str]:
    """F24: montos de los textos dados (la minuta, según el llamador)."""
    return frozenset(m for texto in textos for m in montos_de(norm(texto)))


_NUMEROS = {
    **{
        w: i
        for i, w in enumerate(
            "CERO UNO DOS TRES CUATRO CINCO SEIS SIETE OCHO NUEVE DIEZ ONCE DOCE "
            "TRECE CATORCE QUINCE DIECISEIS DIECISIETE DIECIOCHO DIECINUEVE VEINTE "
            "VEINTIUNO VEINTIDOS VEINTITRES VEINTICUATRO VEINTICINCO VEINTISEIS "
            "VEINTISIETE VEINTIOCHO VEINTINUEVE".split()
        )
    },
    **{
        w: 30 + 10 * i
        for i, w in enumerate(
            "TREINTA CUARENTA CINCUENTA SESENTA SETENTA OCHENTA NOVENTA".split()
        )
    },
    **{
        w: 100 * (i + 1)
        for i, w in enumerate(
            "CIENTO DOSCIENTOS TRESCIENTOS CUATROCIENTOS QUINIENTOS SEISCIENTOS "
            "SETECIENTOS OCHOCIENTOS NOVECIENTOS".split()
        )
        for w in {w, w[:-2] + "AS"}
    },
    "UN": 1,
    "UNA": 1,
    "VEINTIUN": 21,
    "VEINTIUNA": 21,
    "CIEN": 100,
    "MIL": 1000,
    "MILLON": 10**6,
    "MILLONES": 10**6,
}
RE_CIFRA_PARENTESIS = re.compile(
    r"\(\s*(?:(?:S/\.?|US\$|\$)\s*)?(\d[\d,]*)(?:\.(\d{2}))?\s*(%)?\s*\)"
)
# F30: «… SOLES (S/ 9.99)», «… DOLARES (US$ 9.99)» y «… POR CIENTO (9%)».
_RE_MONEDA_EN_LETRAS = re.compile(
    r"\s(?:(?:NUEVOS )?SOLES|DOLARES(?: AMERICANOS| DE LOS ESTADOS UNIDOS DE"
    r" (?:NORTE ?)?AMERICA)?)$"
)


def numero_en_letras(palabras) -> int | None:
    """Valor de un número en letras (0 a 999 999 999 999); None si una palabra
    no es numérica."""
    millones = total = actual = 0
    for w in palabras:
        if w == "Y":
            continue
        if w not in _NUMEROS:
            return None
        if w in {"MILLON", "MILLONES"}:
            millones += (total + actual or 1) * 10**6
            total = actual = 0
        elif w == "MIL":
            total += (actual or 1) * 1000
            actual = 0
        else:
            actual += _NUMEROS[w]
    return millones + total + actual


def _cola_en_letras(texto: str) -> tuple[int, list[str]] | None:
    """F19: (posición, palabras) del número en letras con que termina ``texto``."""
    palabras = list(re.finditer(r"\S+", texto))
    inicio = len(palabras)
    # ponytail: una palabra mal escrita se reconoce por similitud >= 75; si
    # entra ruido, subir el umbral o exigirla entre dos palabras numericas.
    while inicio and (
        (w := palabras[inicio - 1].group()) == "Y"
        or w in _NUMEROS
        or (
            len(w) >= 3
            and process.extractOne(
                w, _NUMEROS.keys(), scorer=fuzz.ratio, score_cutoff=75
            )
        )
    ):
        inicio -= 1
    while inicio < len(palabras) and palabras[inicio].group() == "Y":
        inicio += 1
    span = [p.group() for p in palabras[inicio:]]
    if not any(w in _NUMEROS for w in span):
        return None
    return palabras[inicio].start(), span


def _separar_decimales(antes: str) -> tuple[str, str]:
    """F30: (parte entera, decimales) de «… Y 50/100», «… PUNTO CERO CINCO» o
    «… COMA CINCO»; sin decimales, «00»."""
    if centimos := re.search(r"\s(?:Y|CON) (\d{2})/100$", antes):
        return antes[: centimos.start()], centimos[1]
    for separador in (" PUNTO ", " COMA "):
        entero, _, cola = antes.rpartition(separador)
        palabras = cola.split()
        if entero and palabras and all(w in _NUMEROS or w == "Y" for w in palabras):
            ceros = next(
                (i for i, w in enumerate(palabras) if w != "CERO"), len(palabras)
            )
            resto = palabras[ceros:]
            return entero, "0" * ceros + (str(numero_en_letras(resto)) if resto else "")
    return antes, "00"


Leido = tuple[int, int | None, str]
# (posición donde empiezan las letras, valor o None si no se lee, decimales)


def _leer_letras(texto: str) -> Leido | None:
    """F30: el número en letras, con decimales, con que termina ``texto``."""
    texto, decimales = _separar_decimales(texto)
    if (cola := _cola_en_letras(texto)) is None:
        return None
    inicio, span = cola
    return inicio, numero_en_letras(span), decimales


def _sin_unidad(texto: str, porcentaje: str | None) -> str | None:
    """Las letras sin «POR CIENTO» ni moneda; None si el % no se dice en letras."""
    if porcentaje:
        return (
            texto.removesuffix(" POR CIENTO") if texto.endswith(" POR CIENTO") else None
        )
    moneda = _RE_MONEDA_EN_LETRAS.search(texto)
    return texto[: moneda.start()] if moneda else texto


def _mismo_numero(leido: Leido, cifra: str, decimales: str | None) -> bool:
    """¿Las letras valen lo mismo que la cifra? 0.5 == 0.50."""
    _, valor, decimales_letras = leido
    return valor is not None and (valor, decimales_letras.rstrip("0")) == (
        int(cifra.replace(",", "")),
        (decimales or "").rstrip("0"),
    )


def _cifra(m: re.Match) -> str:
    return m[1] + (f".{m[2]}" if m[2] else "")


_LETRAS_ENTRE_PARENTESIS = r"\s*\(([A-ZÑ][A-ZÑ ]*(?:\d{2}/100[A-ZÑ ]*)?)\)"
RE_LETRAS_PARENTESIS = re.compile(
    r"(?<![\d,.])(\d[\d,]*)(?:\.(\d{2}))?\s*(%)?" + _LETRAS_ENTRE_PARENTESIS
)
# F30: el orden inverso, «S/ 1,500.00 (MIL QUINIENTOS Y 00/100 SOLES)».


def _numeros_en_letras(d: str) -> list[str]:
    """F19: letras y su cifra entre paréntesis (o al revés) que no valen lo mismo."""
    obs = []
    for m in RE_CIFRA_PARENTESIS.finditer(d):
        base = max(0, m.start() - 300)  # el número en letras más largo cabe
        antes = _sin_unidad(d[base : m.start()].rstrip(), m[3])
        leido = _leer_letras(antes) if antes else None
        if leido and not _mismo_numero(leido, m[1], m[2]):
            hallado = d[base + leido[0] : m.end()]
            obs.append(
                f"[NUMERO_EN_LETRAS] «{hallado}» debe decir «{_cifra(m)}{m[3] or ''}»"
            )
    for m in RE_LETRAS_PARENTESIS.finditer(d):
        letras = _sin_unidad(m[4].strip(), m[3])
        leido = _leer_letras(letras) if letras else None
        # Las letras deben ser todo el paréntesis: «(DEL CODIGO CIVIL)» no es número.
        if leido and leido[0] == 0 and not _mismo_numero(leido, m[1], m[2]):
            obs.append(
                f"[NUMERO_EN_LETRAS] «{m[0]}» debe decir «{_cifra(m)}{m[3] or ''}»"
            )
    return obs


_UNIDAD_AREA = r"\s*(?:M2|MTS?\.?\s?2|METROS CUADRADOS)\.?"
RE_AREA_PARENTESIS = re.compile(
    r"\(\s*(\d[\d,]*)(?:\.(\d{1,2}))?" + _UNIDAD_AREA + r"\s*\)"
)
RE_AREA_LETRAS = re.compile(
    r"(?<![\d,.])(\d[\d,]*)(?:\.(\d{1,2}))?" + _UNIDAD_AREA + _LETRAS_ENTRE_PARENTESIS
)


def _leer_area(texto: str) -> Leido | None:
    """F30: el área en letras con que termina ``texto``: «… METROS CUADRADOS»,
    con decimales como en ``_separar_decimales`` o «… CON CINCUENTA DECIMETROS
    CUADRADOS» (1 dm² = 0.01 m²)."""
    decimales = None
    if texto.endswith(" DECIMETROS CUADRADOS"):
        leido = _leer_letras(texto.removesuffix(" DECIMETROS CUADRADOS"))
        if leido is None:
            return None
        inicio, decimetros, _ = leido
        texto = re.sub(r"\s(?:Y|CON)$", "", texto[:inicio].rstrip())
        decimales = f"{decimetros:02d}" if decimetros is not None else "?"
    if not texto.endswith(" METROS CUADRADOS"):
        return None
    leido = _leer_letras(texto.removesuffix(" METROS CUADRADOS"))
    if leido is None:
        return None
    inicio, metros, decimales_letras = leido
    return inicio, metros, decimales or decimales_letras


def _areas_en_letras(d: str) -> list[str]:
    """F30: área en letras y su cifra en m² (en cualquier orden) que no valen lo mismo."""
    obs = []
    for m in RE_AREA_PARENTESIS.finditer(d):
        base = max(0, m.start() - 300)
        leido = _leer_area(d[base : m.start()].rstrip(" ,"))
        if leido and not _mismo_numero(leido, m[1], m[2]):
            hallado = d[base + leido[0] : m.end()]
            obs.append(f"[AREA] «{hallado}» debe decir «{_cifra(m)} M2»")
    for m in RE_AREA_LETRAS.finditer(d):
        leido = _leer_area(m[3].strip())
        if leido and leido[0] == 0 and not _mismo_numero(leido, m[1], m[2]):
            obs.append(f"[AREA] «{m[0]}» debe decir «{_cifra(m)} M2»")
    return obs


_ORDINALES = {
    "PRIMER": 1, "SEGUND": 2, "TERCER": 3, "CUART": 4, "QUINT": 5, "SEXT": 6,
    "SEPTIM": 7, "SETIM": 7, "OCTAV": 8, "NOVEN": 9, "DECIM": 10, "UNDECIM": 11,
    "DUODECIM": 12, "VIGESIM": 20, "TRIGESIM": 30,
}  # fmt: skip
_RAIZ_ORDINAL = "|".join(sorted(_ORDINALES, key=len, reverse=True))
RE_CLAUSULA = re.compile(
    rf"^(?:CLAUSULA\s+)?((?:(?:DECIM|VIGESIM|TRIGESIM)[AO]\s*)?(?:{_RAIZ_ORDINAL})([AO]))"
    r"\s*(?:\.-|[.:-])"
)
# Rótulo al inicio de línea y con signo: «PRIMERA.-», «CLAUSULA SEGUNDA:».
# Tras «.-» y «)» el espacio es opcional («B.-SUSCRIBIR»); tras «.» y «-» no,
# para no leer como inciso una cifra decimal o una sigla.
RE_INCISO = re.compile(r"^([A-Z]|\d{1,2}|[IVX]{1,6})\s?(\)|\.-|\.(?=\s)|-(?=\s))\s?")
_LETRAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_TEXTO_ROMANO = {valor: romano for romano, valor in _ROMANOS.items()}


def _texto_ordinal(n: int, genero: str) -> str:
    decena, unidad = divmod(n, 10)
    raices = [("DECIM", "VIGESIM", "TRIGESIM")[decena - 1]] if decena else []
    raices += [next(r for r, v in _ORDINALES.items() if v == unidad)] if unidad else []
    return " ".join(r + genero for r in raices)


def _clase_inciso(simbolo: str, ultimos: dict) -> tuple[str, int] | None:
    """(clase, valor) del inciso; «I», «V» y «X» son letra o romano según cuál
    continúa su secuencia."""
    if simbolo.isdigit():
        return "NUMERO", int(simbolo)
    opciones = [
        ("LETRA", _LETRAS.index(simbolo) + 1) if len(simbolo) == 1 else None,
        ("ROMANO", _ROMANOS[simbolo]) if simbolo in _ROMANOS else None,
    ]
    opciones = [o for o in opciones if o]
    for clase, valor in opciones:
        if ultimos.get(clase, 0) + 1 == valor:
            return clase, valor
    return opciones[0] if opciones else None


def _rompe_secuencia(ultimos: dict, clase: str, valor: int) -> int | None:
    """El valor esperado si ``valor`` rompe su secuencia; None si la sigue o la
    empieza (1, o primera vez que aparece la clase)."""
    anterior, ultimos[clase] = ultimos.get(clase), valor
    if valor == 1 or anterior is None or valor == anterior + 1:
        return None
    return anterior + 1


def _correlativos(destino: str) -> list[str]:
    """F30: cláusulas (PRIMERA, SEGUNDA…) e incisos (a, b…; 1, 2…; I, II…) que
    saltan o repiten su número. Un 1 empieza una secuencia nueva; cada
    cláusula reinicia sus incisos. Femenino y masculino son secuencias aparte,
    salvo que el ordinal continúe la numeración general (SEGUNDO, TERCERA…)."""
    obs = []
    clausulas, incisos, clausula = {}, {}, ""
    for linea in destino.splitlines():
        t = norm(linea)
        if m := RE_CLAUSULA.match(t):
            ordinal, genero = re.sub(r"\s+", " ", m[1]), m[2]
            valor = sum(_ORDINALES[r] for r in re.findall(_RAIZ_ORDINAL, ordinal))
            general, clausulas["*"] = clausulas.get("*", 0), valor
            esperado = _rompe_secuencia(clausulas, genero, valor)
            if esperado and valor != general + 1:
                # El otro género avanzó la numeración: la falta es contra ella.
                esperado = general + 1 if esperado <= general else esperado
                correcto = _texto_ordinal(esperado, genero)
                obs.append(
                    f"[CORRELATIVO] «{m[0]}» debe decir "
                    f"«{m[0][: m.start(1)]}{correcto}{m[0][m.end(1) :]}»"
                )
            incisos, clausula = {}, ordinal
        elif (m := RE_INCISO.match(t)) and (inciso := _clase_inciso(m[1], incisos)):
            clase, valor = inciso
            if esperado := _rompe_secuencia(incisos, clase, valor):
                simbolo = {
                    "NUMERO": str(esperado),
                    "LETRA": _LETRAS[esperado - 1] if esperado <= len(_LETRAS) else "?",
                    "ROMANO": _TEXTO_ROMANO.get(esperado, "?"),
                }[clase]
                motivo = f"   (cláusula {clausula})" if clausula else ""
                obs.append(
                    f"[CORRELATIVO] «{m[1]}{m[2]}» debe decir «{simbolo}{m[2]}»{motivo}"
                )
    return obs


_RE_COPROPIEDAD = re.compile(r"COPROPIE|ACCIONES Y DERECHOS|CUOTA IDEAL|PARTICIPACION")
_RE_PORCENTAJE = re.compile(r"(?<![\d.,])(\d{1,3})(?:[.,](\d{1,2}))?\s*%")
_RE_POR_CIENTO = re.compile(r"(?<![A-ZÑ])POR CIENTO(?![A-ZÑ])")


def _cuotas(oracion: str) -> list[tuple[int, int, int]]:
    """(inicio, fin, centésimas) de cada porcentaje; en letras solo si la oración
    no trae cifras con %, para no contar dos veces «50% (CINCUENTA POR CIENTO)»."""
    cuotas = [
        (m.start(), m.end(), int(m[1]) * 100 + int((m[2] or "0").ljust(2, "0")))
        for m in _RE_PORCENTAJE.finditer(oracion)
    ]
    if cuotas:
        return cuotas
    for m in _RE_POR_CIENTO.finditer(oracion):
        leido = _leer_letras(oracion[: m.start()].rstrip())
        if leido and leido[1] is not None:
            inicio, valor, decimales = leido
            centesimas = valor * 100 + int(decimales.ljust(2, "0")[:2])
            cuotas.append((inicio, m.end(), centesimas))
    return cuotas


def _porcentaje(centesimas: int) -> str:
    entero, resto = divmod(centesimas, 100)
    return f"{entero}.{resto:02d}" if resto else str(entero)


def _copropiedad(destino: str) -> list[str]:
    """F30: cuotas de copropiedad de una misma oración que no suman 100 %.

    Vale también un múltiplo de 100 (vendedores y compradores en la misma
    oración) o que una cuota sea la suma de las demás (se transfiere el 50 % y
    se adquiere 25 % y 25 %). Con «CADA UNO» no se puede sumar: se omite.
    ponytail: solo dentro de la oración; si las cuotas se reparten en varias,
    no se detecta. [NEEDS CLARIFICATION] confirmar con escrituras reales.
    """
    obs = []
    for linea in destino.splitlines():
        for oracion in re.split(r"(?<!S/)\.\s+", norm(linea)):
            if not _RE_COPROPIEDAD.search(oracion) or re.search(
                r"CADA UN[AO]", oracion
            ):
                continue
            cuotas = _cuotas(oracion)
            if len(cuotas) < 2:
                continue
            total = sum(c for _, _, c in cuotas)
            tolerancia = len(cuotas)  # redondeo: 33.33 % tres veces suma 99.99 %
            resto = total % 10000
            if min(resto, 10000 - resto) <= tolerancia or any(
                abs(total - 2 * c) <= tolerancia for _, _, c in cuotas
            ):
                continue
            tramo = oracion[cuotas[0][0] : cuotas[-1][1]]
            obs.append(
                f"[COPROPIEDAD] «{tramo}» debe decir «100 %»   "
                f"(las cuotas suman {_porcentaje(total)} %)"
            )
    return obs


_RE_MONTO_OBSERVADO = re.compile(r"\[MONTO\] «(?:US\$ )?([\d,.]+)»")


def _cantidades_observadas(fuente, d: str, previas=()) -> list[str]:
    """F30: precio, tasación, valor o hipoteca del borrador cuya cifra no es la
    de ese mismo concepto en las fuentes. Sin el concepto en las fuentes, nada.
    Una cifra que ``previas`` ya observa como MONTO no se repite."""
    por_concepto = {}
    for concepto, cifra in fuente:
        por_concepto.setdefault(concepto, set()).add(cifra)
    ya_observadas = {m[1] for o in previas if (m := _RE_MONTO_OBSERVADO.match(o))}
    obs = []
    for concepto, cifra in cantidades_de(d):
        esperados = por_concepto.get(concepto, set())
        if (
            not esperados
            or cifra in ya_observadas
            or cifra.replace(",", "") in {e.replace(",", "") for e in esperados}
        ):
            continue
        esperado = min(
            sorted(esperados), key=lambda e, c=cifra: Levenshtein.distance(c, e)
        )
        nombre = concepto.replace("_", " ")
        obs.append(f"[MONTO] «{cifra}» debe decir «{esperado}»   (concepto: {nombre})")
    return obs


def _registrales_observados(fuente, d: str) -> list[str]:
    """F30: zona, registro, oficina y provincia del borrador.

    - La zona existe (I a XIV) y su sede es la de SUNARP.
    - El valor está en las fuentes, si las fuentes traen esa clase. Zona y
      registro son listas cerradas: con un único valor en las fuentes, ese es el
      esperado. Oficina y provincia son texto: «debe decir» solo si se parecen
      (ratio >= 80); una provincia distinta sin parecido no se observa, porque
      el borrador nombra lugares que no están en las fuentes (la notaría).
    """
    por_clase = {}
    for clase, valor in fuente:
        por_clase.setdefault(clase, set()).add(valor)
    obs = []
    for clase, valor, m in datos_registrales(d):
        frase = d[m.start() : m.start(1) + len(valor)]
        if clase == "ZONA":
            numero = _ROMANOS.get(valor, 0)
            if not 1 <= numero <= len(_ZONAS_REGISTRALES):
                obs.append(
                    f"[DATO_REGISTRAL] «{frase}» no coincide con ninguna fuente   "
                    f"(SUNARP tiene {len(_ZONAS_REGISTRALES)} zonas registrales)"
                )
                continue
            sede = _ZONAS_REGISTRALES[numero - 1]
            if m[2] and m[2].replace("CUZCO", "CUSCO") != sede:
                obs.append(
                    f"[DATO_REGISTRAL] «{m[0]}» debe decir "
                    f"«{m[0][: m.start(2) - m.start()]}{sede}»   "
                    f"(sede de la zona registral {valor})"
                )
        esperados = por_clase.get(clase, set())
        if not esperados or valor in esperados:
            continue
        cercano, parecido, _ = process.extractOne(
            valor, sorted(esperados), scorer=fuzz.ratio
        )
        if (clase in {"ZONA", "REGISTRO"} and len(esperados) == 1) or (
            clase in {"OFICINA", "PROVINCIA"} and parecido >= 80
        ):
            obs.append(
                f"[DATO_REGISTRAL] «{frase}» debe decir "
                f"«{frase[: len(frase) - len(valor)]}{cercano}»"
            )
        elif clase != "PROVINCIA":
            obs.append(f"[DATO_REGISTRAL] «{frase}» no coincide con ninguna fuente")
    return obs


def _nombres_por_ventana(conocidos, d: str, ya_vistos) -> list[str]:
    """F19: la ventana del borrador más parecida a cada nombre de las fuentes."""
    # Solo letras: un signo que arrastra el OCR («NOMBRE:») no es una diferencia.
    conocidos = {" ".join(re.findall(r"[A-ZÑ]+", norm(n))) for n in conocidos} - {""}
    tokens = re.findall(r"[A-ZÑ]+", d)
    ventanas = {}
    for n in conocidos:
        k = len(n.split())
        ventanas.setdefault(
            k, [" ".join(tokens[i : i + k]) for i in range(len(tokens) - k + 1)]
        )
    exactos = {
        j
        for n in conocidos
        for i, v in enumerate(ventanas[len(n.split())])
        if v == n
        for j in range(i, i + len(n.split()))
    }
    obs = []
    for n in sorted(conocidos):
        k = len(n.split())
        libres = {
            i: v
            for i, v in enumerate(ventanas[k])
            if exactos.isdisjoint(range(i, i + k))
        }
        m = process.extractOne(n, libres, scorer=fuzz.ratio, score_cutoff=85)
        if m and m[0] not in ya_vistos:
            ya_vistos.add(m[0])
            obs.append(f"[NOMBRE] «{m[0]}» debe decir «{n}»")
    return obs


def _esperado_cercano(valor: str, fuente) -> str:
    """El valor de la fuente a Levenshtein <= 2 (empate: el menor), F19/F22."""
    cercano = min(
        sorted(fuente), key=lambda v: Levenshtein.distance(valor, v), default=None
    )
    if cercano and Levenshtein.distance(valor, cercano) <= 2:
        return f"debe decir «{cercano}»"
    return "no coincide con ninguna fuente"


_RE_CUOTA = re.compile(r"(?:CUOTA\s*(?:N[O°]?\.?\s*)?)?(\d{1,3})(?![\d.,/])")
_RE_FECHA = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")


def _rotulo_fila(linea: str, importes: int) -> str | None:
    """F27: fila de cronograma = varios importes y numero de cuota o fecha."""
    if importes < 2:
        return None
    if m := _RE_CUOTA.match(linea):
        return f"CUOTA {int(m.group(1))}"
    if m := _RE_FECHA.search(linea):
        return f"CUOTA DEL {m.group()}"
    return None


def _montos_por_posicion(minutas: Mapping[str, str], destino: str, umbral: int):
    """F27: por cada importe del borrador, en orden, (esperado, sufijo) del
    importe en la misma posicion de su linea par en la minuta, o None.

    Par: la fila de cronograma con el mismo rotulo o, si no, el parrafo
    (> 80 caracteres, como ``parrafos``) de mayor ``partial_ratio`` >= umbral.
    Con distinto numero de importes no hay par: una insercion no desplaza todo.
    """
    fuente = [
        (linea, ms, pagina)
        for pagina in _paginas(minutas)
        for linea in map(norm, pagina.texto.splitlines())
        if (ms := list(RE_MONTO.finditer(linea)))
    ]
    pares = []
    for linea in map(norm, destino.splitlines()):
        if not (ms := list(RE_MONTO.finditer(linea))):
            continue
        rotulo = _rotulo_fila(linea, len(ms))
        candidatas = [
            f for f in fuente if rotulo and _rotulo_fila(f[0], len(f[1])) == rotulo
        ]
        par = max(candidatas, key=lambda f: fuzz.ratio(linea, f[0]), default=None)
        if par is None and len(linea) > 80:
            par = max(
                (f for f in fuente if len(f[0]) > 80),
                key=lambda f: fuzz.partial_ratio(linea, f[0]),
                default=None,
            )
            if par and fuzz.partial_ratio(linea, par[0]) < umbral:
                par = None
        if par is None or len(par[1]) != len(ms):
            pares += [None] * len(ms)
            continue
        texto, esperados, pagina = par
        for m in esperados:
            concepto = _rotulo_fila(texto, len(esperados)) or " ".join(
                re.findall(r"[\w/]+", RE_MONTO.sub(" ", texto[: m.start()]))[-6:]
            )
            pares.append(
                (
                    _monto(m),
                    f"   (concepto: {concepto}; fuente: {pagina.fuente}, "
                    f"p. {pagina.numero})",
                )
            )
    return pares


def revisar(
    cat: dict[str, set[str]],
    destino: str,
    umbral: int,
    exigibles=None,
    montos_exigibles=None,
    minutas=None,
) -> list[str]:
    """``exigibles`` y ``montos_exigibles`` limitan el FALTA de NOMBRE (F16) y
    de MONTO (F24); ``None`` exige todos. ``minutas`` ({archivo: texto}) activa
    la verificacion de montos por posicion (F27)."""
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
    obs += _nombres_por_ventana(cat["NOMBRE"], d, vistos["NOMBRE"] | vistos_caratula)
    for m in RE_DNI_BORRADOR.finditer(d):
        v, ctx = m.group(1), f"   …{d[max(0, m.start() - 55) : m.end()][-70:]}"
        if len(v) == 8:
            check("DNI", v, ctx)
            continue
        obs.append(f"[DNI] «{v}» {_esperado_cercano(v, cat['DNI'])}{ctx}")
    for v in RE_PARTIDA.findall(d):
        check("PARTIDA", v)
    valores = montos_de(d)
    pares = _montos_por_posicion(minutas or {}, destino, umbral)
    if len(pares) != len(valores):  # un importe partido entre dos lineas
        pares = [None] * len(valores)
    for v, par in zip(valores, pares):
        if par is None:
            check("MONTO", v)
            continue
        vistos["MONTO"].add(v)
        if v != par[0]:
            # el esperado ya queda dicho aqui: no se repite como FALTA
            vistos["MONTO"].add(par[0])
            obs.append(f"[MONTO] «{v}» debe decir «{par[0]}»{par[1]}")
    # F22: cada aparición; el dict legado de cuatro campos no trae RUC ni DIRECCION.
    rucs = cat.get("RUC", frozenset())
    for v in RE_RUC_BORRADOR.findall(d):
        vistos.setdefault("RUC", set()).add(v)
        if v not in rucs:
            obs.append(f"[RUC] «{v}» {_esperado_cercano(v, rucs)}")
    for hallado, esperado in _direcciones_observadas(
        cat.get("DIRECCION", ()), destino, getattr(cat, "vocabulario", Counter())
    ):
        obs.append(f"[DIRECCION] «{hallado}» debe decir «{esperado}»")
    obs += _numeros_en_letras(d)
    # F30: el dict legado no trae cantidades ni datos registrales.
    obs += _cantidades_observadas(getattr(cat, "cantidades", ()), d, obs)
    obs += _areas_en_letras(d)
    obs += _registrales_observados(getattr(cat, "registrales", ()), d)
    obs += _correlativos(destino)
    obs += _copropiedad(destino)

    for campo, vals in cat.items():
        if campo == "DIRECCION":
            continue
        if campo in ("NOMBRE", "RUC") and exigibles is not None:
            vals = vals & exigibles
        if campo == "MONTO" and montos_exigibles is not None:
            vals = vals & montos_exigibles
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
        propios = parrafos(src)
        for i, p in enumerate(propios):
            # subcadena literal: partial_ratio daria 100 y no hay observacion;
            # saltar extractOne evita el costo en borradores largos
            if any(p in d for d in dp):
                continue
            # Basta con UN parrafo sobre el umbral para no observar, y el orden
            # no cambia esa respuesta: se prueban primero los de posicion
            # parecida, que es donde suele estar. La busqueda completa solo
            # corre para los que fallan, porque el mensaje lleva su puntuacion.
            centro = i * len(dp) / len(propios)
            cercanos = sorted(range(len(dp)), key=lambda j, c=centro: abs(j - c))
            if any(fuzz.partial_ratio(p, dp[j], score_cutoff=umbral) for j in cercanos):
                continue
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
