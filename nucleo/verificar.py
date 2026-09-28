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
    ):
        object.__setattr__(self, "personas", tuple(personas))
        object.__setattr__(self, "partidas", frozenset(partidas))
        object.__setattr__(self, "montos", frozenset(montos))
        object.__setattr__(self, "paginas_descartadas", tuple(paginas_descartadas))
        object.__setattr__(
            self, "paginas_no_clasificadas", tuple(paginas_no_clasificadas)
        )
        object.__setattr__(self, "menciones", tuple(menciones))
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
    r"(?:DNI|IDENTIDAD|D[.]N[.]I[.]?|D[.]N[.]1[,.;]?)"
    r"\s*(?:(?:N[O°]?|NUMERO)\s*)?(?:[:,.]\s*)?(?<!\d)(\d{8})(?!\d)"
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
RE_NOMBRE_APELLIDOS = re.compile(
    r"([A-ZÑ][A-ZÑ ]{2,60}),\s*([A-ZÑ][A-ZÑ ]{2,60})"
    r"\s+(?:DE\s+)?NACIONALIDAD"
)

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
    """Lee solo un rótulo al inicio de línea y su propia celda."""
    for linea in raw.splitlines():
        celdas = re.split(r"\s{2,}", linea.strip())
        primera = celdas[0]
        rotulo, _, valor = primera.partition(":")
        if norm(rotulo) != etiqueta:
            continue
        valor = valor.strip() or (celdas[1].strip() if len(celdas) > 1 else "")
        return valor or None
    return None


def _fecha_reniec(valor: str | None) -> date | None:
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
    "DPTO": "DEPARTAMENTO",
    "INT": "INTERIOR",
    "N": "NUMERO",
    "Nº": "NUMERO",
    "N°": "NUMERO",
    "SN": "SIN NUMERO",
}


def _clausula_persona(texto: str, nombre: str) -> str | None:
    t = "\n".join(norm(linea) for linea in texto.splitlines())
    match = re.search(rf"(?<![A-ZÑ]){re.escape(_nombre_clave(nombre))}(?![A-ZÑ])", t)
    if not match:
        return None
    limites = list(re.finditer(r"\.\s+|\n", t[: match.start()]))
    inicio = limites[-1].end() if limites else 0
    if not t[inicio : match.start()].strip() and limites:
        inicio = limites[-2].end() if len(limites) > 1 else 0
    fin = re.search(r"\.\s+|\n", t[match.end() :])
    return t[inicio : match.end() + fin.start() if fin else len(t)]


def _direccion_tokens(texto: str) -> Counter:
    sin_tildes = "".join(
        c
        for c in unicodedata.normalize("NFKD", texto.upper())
        if not unicodedata.combining(c)
    )
    sin_tildes = re.sub(r"\bS\s*/\s*N\b", " SN ", sin_tildes)
    sin_tildes = re.sub(r"N[°º]", " N ", sin_tildes)
    tokens = re.findall(r"[A-Z0-9]+", sin_tildes)
    return Counter(
        palabra for token in tokens for palabra in _VIAS.get(token, token).split()
    )


def revisar_persona_ampliada(
    cat: Catalogo, borrador: str, hoy: date | None = None
) -> tuple[dict, ...]:
    """Observaciones F12 puras: la fecha de referencia siempre llega del llamador."""
    observaciones = []
    for persona in cat.personas:
        if (
            persona.estado != "CONFIRMADA"
            or not persona.documento
            or not persona.nombre
        ):
            continue
        clausula = _clausula_persona(borrador, persona.nombre)
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
            if not any(
                direccion <= _direccion_tokens(oracion) for oracion in oraciones
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
        personas_pagina = _personas_de_pagina(pagina, tipo)
        if tipo == "DESCONOCIDA" and personas_pagina:
            no_clasificadas.append(PaginaDescartada(pagina.fuente, pagina.numero, tipo))
        for persona in personas_pagina:
            if tipo in _TIPOS_ANCLA and persona.nombre and persona.documento:
                anclas.append(persona)
                tipos.append(tipo)
            else:
                resto.append(persona)
    personas, menciones = _pegar(unificar_personas(anclas, tipos), resto)
    return Catalogo(
        personas,
        frozenset(partidas),
        frozenset(montos),
        tuple(descartadas),
        tuple(no_clasificadas),
        menciones,
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
    """Nombres de las anclas y de los textos dados (la minuta, según el llamador)."""
    return frozenset(p.nombre for p in cat.personas) | {
        n for texto in textos for n in catalogo({"exigible": texto})["NOMBRE"]
    }


def revisar(
    cat: dict[str, set[str]], destino: str, umbral: int, exigibles=None
) -> list[str]:
    """``exigibles`` limita el FALTA de NOMBRE; ``None`` exige todos (F16)."""
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
        if campo == "NOMBRE" and exigibles is not None:
            vals = vals & exigibles
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
