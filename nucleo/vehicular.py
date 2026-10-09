"""F43: transferencia vehicular.

Compara el acta con la boleta informativa SUNARP (placa, partida, propietario y
características) y con el monto de los cheques; el precio debe constar en el
acta. Devuelve observaciones con el formato de ``verificar.revisar`` para
reutilizar su presentación y correcciones.
"""

import re
from collections.abc import Mapping

from rapidfuzz import fuzz

from nucleo.verificar import SEPARADOR_PAGINA, montos_de, norm

_NUM = r"(?:N\W{0,2}O?\.?|NRO\.?|NUMERO)\s*"
# Rótulo normalizado de la boleta -> campo. El OCR lee «N°» como N', NO o N.
_ROTULOS = (
    ("PLACA", re.compile(r"PLACA")),
    ("PARTIDA", re.compile(rf"{_NUM}PARTIDA")),
    ("MARCA", re.compile(r"MARCA")),
    ("MODELO", re.compile(r"MODELO")),
    ("ANIO_FABRICACION", re.compile(r"A[ÑN]O FAB\.?")),
    ("ANIO_MODELO", re.compile(r"A[ÑN]O MOD\.?")),
    ("SERIE", re.compile(rf"{_NUM}SERIE")),
    ("VIN", re.compile(rf"{_NUM}DE VIN")),
    ("MOTOR", re.compile(rf"{_NUM}MOTOR")),
    ("COLOR", re.compile(r"COLOR 1")),
    ("CATEGORIA", re.compile(r"CATEGORIA")),
    ("CARROCERIA", re.compile(r"CARROCERIA")),
    ("PROPIETARIO", re.compile(r"NOMBRE")),
)
# Características que solo se revisan si el acta las menciona. Las de código se
# comparan sin espacios ni guiones.
_CODIGOS = {"SERIE", "VIN", "MOTOR", "ANIO_FABRICACION", "ANIO_MODELO"}
_MENCION = {
    "MARCA": r"MARCA",
    "MODELO": r"MODELO",
    "ANIO_FABRICACION": r"A[ÑN]O DE FABRICACION",
    "ANIO_MODELO": r"A[ÑN]O(?: DE)? MODELO",
    "SERIE": rf"(?:{_NUM}(?:DE )?)?SERIE",
    "VIN": r"VIN",
    "MOTOR": rf"(?:{_NUM}(?:DE )?)?MOTOR",
    "COLOR": r"COLOR",
    "CATEGORIA": r"CATEGORIA",
    "CARROCERIA": r"CARROCERIA",
}
_RE_PLACA = re.compile(
    rf"\bPLACA(?: DE RODAJE)?\s*[:.]?\s*(?:{_NUM})?([A-Z0-9]{{1,4}}(?:-?[A-Z0-9]{{2,4}})?)\b"
)
_RE_PARTIDA = re.compile(
    rf"\bPARTIDA(?: REGISTRAL| ELECTRONICA)?\s*(?:{_NUM})?[:.]?\s*(\d{{6,9}})\b"
)
_CERCA_DE_PLACA = 400  # caracteres: la partida del vehículo sigue a su placa
# Las características se buscan junto a la placa: más lejos, «número de serie»
# es el de la foja notarial.
_ZONA_PLACA = (200, 800)
_RE_CHEQUE = re.compile(r"CHE[QD]UE|PAGUE(?:SE)? A LA ORDEN|A LA ORDEN DE")
# El OCR lee el importe del cheque con «.» de miles: *****70.000.00
_RE_IMPORTE_CHEQUE = re.compile(r"\*{2,}\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})\b")
_RE_PRECIO = re.compile(r"\bPRECIO\b")
_CERCA_DEL_PRECIO = 400  # caracteres: «EL PRECIO ... ES DE: ... (US$ 0.00)»


def _clave(valor: str) -> str:
    return re.sub(r"[^A-Z0-9Ñ]", "", valor)


def _pares(linea: str):
    """(rótulo, valor) de una fila «Rótulo  : valor  Rótulo  : valor»."""
    celdas = [c.strip() for c in re.split(r"\s{2,}", linea) if c.strip()]
    i = 0
    while i < len(celdas):
        celda = celdas[i]
        if i + 1 < len(celdas) and celdas[i + 1].startswith(":"):
            yield celda, celdas[i + 1][1:]
            i += 1
        elif ":" in celda and not celda.startswith(":"):
            yield tuple(celda.split(":", 1))
        i += 1


def boletas(fuentes: Mapping[str, str]) -> list[dict]:
    """Datos de cada boleta informativa vehicular entre las fuentes."""
    salida = []
    for nombre, texto in fuentes.items():
        datos = {}
        for pagina in texto.split(SEPARADOR_PAGINA):
            plano = norm(pagina)
            if (
                "BOLETA INFORMATIVA" not in plano
                and "CARACTERISTICAS DEL VEHICULO" not in plano
            ):
                continue
            for linea in pagina.splitlines():
                for rotulo, valor in _pares(linea):
                    valor = norm(valor).strip(" :")
                    if not valor or "#" in valor:
                        continue
                    for campo, patron in _ROTULOS:
                        if patron.fullmatch(norm(rotulo)):
                            if campo == "PROPIETARIO":
                                datos.setdefault(campo, [])
                                if valor not in datos[campo]:
                                    datos[campo].append(valor)
                            else:
                                datos.setdefault(campo, valor)
                            break
        if datos.get("PLACA"):
            salida.append({"fuente": nombre, **datos})
    return salida


def cheques(fuentes: Mapping[str, str]) -> list[dict]:
    """Importe legible de cada cheque entre las fuentes."""
    salida = []
    for texto in fuentes.values():
        for pagina in texto.split(SEPARADOR_PAGINA):
            plano = norm(pagina)
            if not _RE_CHEQUE.search(plano):
                continue
            importe = _RE_IMPORTE_CHEQUE.search(plano)
            if importe:
                digitos = re.sub(r"\D", "", importe.group(1))
                cifra = f"{int(digitos[:-2]):,}.{digitos[-2:]}"
                salida.append(
                    f"US$ {cifra}"
                    if re.search(r"DOLARES|US\$", plano) and "SOLES" not in plano
                    else cifra
                )
    return salida


def _placa(boleta, d):
    esperado = boleta["PLACA"]
    mencionadas = [m for m in _RE_PLACA.finditer(d) if re.search(r"\d", m.group(1))]
    if any(_clave(m.group(1)) == _clave(esperado) for m in mencionadas):
        return []
    if mencionadas:
        return [
            f"[PLACA] «{hallado}» debe decir «{esperado}»"
            for hallado in dict.fromkeys(m.group(1) for m in mencionadas)
        ]
    return [
        f"[PLACA] FALTA: «{esperado}» esta en las fuentes y no aparece en el destino"
    ]


def _partida(boleta, d):
    esperado = boleta.get("PARTIDA")
    if not esperado or re.search(rf"\b{esperado}\b", d):
        return []
    placas = [m.start() for m in _RE_PLACA.finditer(d)]
    cercanas = [
        m.group(1)
        for m in _RE_PARTIDA.finditer(d)
        if any(0 <= m.start() - p <= _CERCA_DE_PLACA for p in placas)
    ]
    if cercanas:
        return [f"[PARTIDA] «{cercanas[0]}» debe decir «{esperado}»"]
    return [
        f"[PARTIDA] FALTA: «{esperado}» esta en las fuentes y no aparece en el destino"
    ]


def _caracteristicas(boleta, d):
    obs = []
    antes, despues = _ZONA_PLACA
    zonas = [
        d[max(0, m.start() - antes) : m.start() + despues]
        for m in _RE_PLACA.finditer(d)
    ]
    for campo, mencion in _MENCION.items():
        esperado = boleta.get(campo)
        if not esperado:
            continue
        patron = rf"\b{mencion}\b\s*(?:{_NUM})?[:.]?\s*([A-Z0-9Ñ][A-Z0-9Ñ /-]*?)(?=\s*(?:[,;=]|\.\s|\.?$))"
        for m in (m for zona in zonas for m in re.finditer(patron, zona)):
            hallado = m.group(1).strip()
            iguales = (
                _clave(hallado) == _clave(esperado)
                if campo in _CODIGOS
                else " ".join(hallado.split()) == " ".join(esperado.split())
            )
            if not iguales:
                obs.append(f"[VEHICULO] «{hallado}» debe decir «{esperado}»")
    return obs


def _propietarios(boleta, d):
    obs = []
    tokens = list(re.finditer(r"[A-ZÑ0-9]+", d))
    for esperado in boleta.get("PROPIETARIO", ()):
        buscado = " ".join(re.findall(r"[A-ZÑ0-9]+", esperado))
        k = len(buscado.split())
        if not k:
            continue
        mejor = None
        for i in range(len(tokens) - k + 1):
            ventana = " ".join(t.group() for t in tokens[i : i + k])
            if ventana == buscado:
                mejor = None
                break
            puntaje = fuzz.ratio(ventana, buscado)
            if puntaje >= 85 and (mejor is None or puntaje > mejor[0]):
                mejor = (puntaje, tokens[i].start(), tokens[i + k - 1].end())
        else:
            if mejor is None:
                obs.append(
                    f"[PROPIETARIO] FALTA: «{esperado}» esta en las fuentes "
                    "y no aparece en el destino"
                )
            else:
                _, inicio, fin = mejor
                fin += esperado.endswith(".") and d[fin : fin + 1] == "."
                obs.append(f"[PROPIETARIO] «{d[inicio:fin]}» debe decir «{esperado}»")
    return obs


def _cheques(montos_cheques, d):
    """El monto transferido con cada cheque debe constar en el acta (decisión
    del usuario, 2026-10-09: no se comparan número, banco ni beneficiario)."""
    montos = set(montos_de(d))
    return [
        "[CHEQUE] FALTA: "
        f"«{monto if monto.startswith('US$') else f'S/ {monto}'}» "
        "esta en las fuentes y no aparece en el destino"
        for monto in montos_cheques
        if monto not in montos
    ]


def _precio(d):
    """El precio debe constar en el acta, aunque se pague por transferencia."""
    if any(
        montos_de(d[m.end() : m.end() + _CERCA_DEL_PRECIO])
        for m in _RE_PRECIO.finditer(d)
    ):
        return []
    return ["[PRECIO] FALTA: «Precio de la transferencia» no aparece en el acta"]


def revisar(fuentes: Mapping[str, str], destino: str) -> list[str]:
    """Observaciones del acta frente a las boletas y los cheques de las fuentes."""
    d = norm(destino)
    obs = []
    for boleta in boletas(fuentes):
        obs += _placa(boleta, d)
        obs += _partida(boleta, d)
        obs += _caracteristicas(boleta, d)
        obs += _propietarios(boleta, d)
    obs += _precio(d)
    obs += _cheques(cheques(fuentes), d)
    return list(dict.fromkeys(obs))
