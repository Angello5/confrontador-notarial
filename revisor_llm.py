"""Capa de prosa: el modelo SOLO detecta ortografia/gramatica, nunca datos duros.

Todo hallazgo pasa tres filtros mecanicos antes de salir. Sin ellos el modelo
emite valores que no existen en el documento (alucinaciones), correcciones
identicas al error, y valores "correctos" que no estan en ninguna fuente.

La key se lee de GEMINI_API_KEY o del .env local. Nunca se imprime.
"""
import json
import os
import re
import time
import unicodedata
import urllib.request
from pathlib import Path

from extraer import _cacheado

MODELO = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
ENV_NOTARIA = Path(__file__).parent / ".env"

INSTRUCCIONES = """Eres corrector de estilo de escrituras publicas peruanas.

Devuelve SOLO errores de ORTOGRAFIA, TILDES, GRAMATICA o CONCORDANCIA en la
prosa: palabras mal escritas, letras faltantes o sobrantes, tildes incorrectas.

NO reportes nunca:
- numeros: DNI, partidas, montos, fechas, numeros de calle, folios
- nombres propios de personas
- mayusculas, formato, orden de secciones o estilo de redaccion

Reglas de salida:
- "encontrado" debe ser el texto EXACTO tal como aparece en el documento
- "correccion" debe ser distinto de "encontrado"
- si no estas seguro de que sea un error, omitelo

Responde JSON: {"hallazgos":[{"encontrado":"...","correccion":"...","motivo":"..."}]}
"""


def _key() -> str:
    if k := os.environ.get("GEMINI_API_KEY"):
        return k
    for linea in ENV_NOTARIA.read_text().splitlines():
        if linea.startswith("GEMINI_API_KEY="):
            return linea.split("=", 1)[1].strip().strip("'\"")
    raise RuntimeError("falta GEMINI_API_KEY")


def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip()


def _sin_tildes(t: str) -> str:
    d = unicodedata.normalize("NFKD", t)
    return "".join(c for c in d if not unicodedata.combining(c)).upper()


def _tildar(t: str) -> bool:
    return any(unicodedata.combining(c) for c in unicodedata.normalize("NFKD", t))


def _solo_agrega_tilde(enc: str, cor: str) -> bool:
    """Poner tildes a MAYUSCULAS es estilo, no error: la escritura final las deja
    sin tilde. En cambio una tilde MAL PUESTA (OCUPACION con acento grave) si lo
    es, y ahi el texto encontrado ya trae tilde, asi que no cae en esta regla."""
    return (_sin_tildes(enc) == _sin_tildes(cor) and not _tildar(enc)
            and _tildar(cor) and enc == enc.upper())


def consultar(texto: str, modelo: str = None) -> list[dict]:
    """Crudo, sin filtrar. Temperatura 0 aunque no garantice determinismo."""
    cuerpo = json.dumps({
        "system_instruction": {"parts": [{"text": INSTRUCCIONES}]},
        "contents": [{"parts": [{"text": texto}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }).encode()
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{modelo or MODELO}:generateContent?key={_key()}")
    req = urllib.request.Request(url, cuerpo, {"Content-Type": "application/json"})
    # 503 "high demand" es rutinario y transitorio; sin reintento se pierde la corrida
    # entera, que es justo lo que le pasa a la rama en produccion.
    for intento in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                datos = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or intento == 3:
                raise
            time.sleep(2 ** intento * 5)
    partes = datos["candidates"][0]["content"]["parts"]
    return json.loads("".join(p.get("text", "") for p in partes)).get("hallazgos", [])


def filtrar(crudos: list[dict], documento: str, fuentes: str) -> tuple[list[dict], list[dict]]:
    """Devuelve (aceptados, descartados con su motivo). Los tres filtros del diseño:

    1. lo señalado tiene que existir literalmente en el documento
    2. la correccion tiene que ser distinta del error
    3. si la correccion es un dato duro, manda el verificador determinista
    """
    doc, ok, fuera = _norm(documento), [], []

    def tirar(h, motivo):
        fuera.append(h | {"descartado_por": motivo})

    for h in crudos:
        enc, cor = _norm(str(h.get("encontrado", ""))), _norm(str(h.get("correccion", "")))
        if not enc or not cor:
            tirar(h, "campo vacio")
        elif enc not in doc:
            tirar(h, "no existe en el documento")            # alucinacion
        elif enc == cor:
            tirar(h, "correccion identica al error")         # payload inservible
        elif re.search(r"\d", enc + cor):
            tirar(h, "dato numerico, lo decide la regla")    # el 248
        elif _solo_agrega_tilde(enc, cor):
            tirar(h, "tilde sobre mayusculas, estilo notarial")
        elif cor.upper() in fuentes and enc.upper() not in fuentes and len(cor) > 3:
            ok.append(h | {"encontrado": enc, "correccion": cor, "respaldo": "en las fuentes"})
        else:
            ok.append(h | {"encontrado": enc, "correccion": cor, "respaldo": "solo prosa"})
    return ok, fuera


def revisar_prosa(documento: str, fuentes: str = "", modelo: str = None,
                  cache: bool = True) -> tuple[list, list]:
    """El modelo no es determinista ni a temperatura 0: dos corridas sobre el mismo
    borrador dan listas distintas. Cachear por (modelo, documento) no arregla la
    causa, pero hace que el mismo expediente devuelva siempre lo mismo, que es lo
    que un notario necesita para sostener un criterio."""
    m = modelo or MODELO
    pedir = (lambda: consultar(documento, m)) if not cache else \
        (lambda: _cacheado(f"{m}\n{documento}".encode(), lambda: consultar(documento, m)))
    return filtrar(pedir(), documento, _sin_tildes(fuentes))
