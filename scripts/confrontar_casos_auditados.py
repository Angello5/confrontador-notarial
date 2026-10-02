"""Confronta los casos privados extraídos y solo divulga métricas agregadas.

Requiere `scripts/auditar_casos_ocr.py`. Es una medición diagnóstica del núcleo:
las reglas se calculan incluso si el aviso de correspondencia bloquearía la UI.
Los roles inferidos y los hallazgos requieren validación humana.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nucleo import verificar  # noqa: E402


BASE = ROOT / "expedientes_locales" / "auditoria-20261002"
MINUTAS = {"C05": {"D003"}, "C06": {"D002"}, "C07": {"D002"}, "C09": {"D004"}}


def confrontar(carpeta: Path):
    textos = {}
    for ruta in sorted(carpeta.glob("D*.texto.txt")):
        if not re.fullmatch(r"D\d{3}\.texto\.txt", ruta.name):
            continue
        identificador = ruta.name.split(".")[0]
        textos[identificador] = ruta.read_text(encoding="utf-8")
    if "D001" not in textos:
        return {"caso": carpeta.name, "estado": "sin_borrador_extraido"}
    originales = {
        p.stem: p
        for p in carpeta.iterdir()
        if p.is_file() and re.fullmatch(r"D\d{3}", p.stem)
    }
    esperados = set(originales) - {"D001"}
    faltantes = sorted(esperados - set(textos))
    fuentes = {
        originales[k].name: v
        for k, v in textos.items()
        if k != "D001" and k in originales and v.strip()
    }
    if not fuentes:
        return {
            "caso": carpeta.name,
            "estado": "sin_fuentes",
            "faltantes": len(faltantes),
        }
    minutas = {
        originales[k].name: textos[k]
        for k in MINUTAS.get(carpeta.name, set())
        if k in textos and k in originales
    }
    try:
        catalogo = verificar.catalogo(fuentes)
        aviso = verificar.diagnostico(fuentes, textos["D001"])
        personas = verificar.comparar_personas(catalogo, textos["D001"])
        reglas = verificar.revisar(
            catalogo,
            textos["D001"],
            88,
            verificar.nombres_exigibles(catalogo, list(minutas.values())),
            verificar.montos_exigibles(list(minutas.values())),
            minutas,
        )
        reglas += verificar.revisar_parrafos(list(minutas.values()), textos["D001"], 88)
        tipos = Counter(
            (re.match(r"\[([^]]+)\]", r) or [None, "OTRO"])[1] for r in reglas
        )
        return {
            "caso": carpeta.name,
            "estado": "evaluado",
            "fuentes": len(fuentes),
            "fuentes_faltantes": len(faltantes),
            "aviso_correspondencia": bool(aviso),
            "personas_catalogo": len(catalogo.personas),
            "partidas_catalogo": len(catalogo.partidas),
            "montos_catalogo": len(catalogo.montos),
            "paginas_descartadas": len(catalogo.paginas_descartadas),
            "paginas_no_clasificadas": len(catalogo.paginas_no_clasificadas),
            "comparaciones_personas": len(personas),
            "observaciones_regla": len(reglas),
            "tipos_regla": dict(tipos),
        }
    except Exception as error:
        return {
            "caso": carpeta.name,
            "estado": "error",
            "tipo_error": type(error).__name__,
            "fuentes_faltantes": len(faltantes),
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--caso", action="append")
    args = parser.parse_args()
    carpetas = sorted(
        p
        for p in BASE.iterdir()
        if p.is_dir() and p.name != "cache" and p.name != "deps"
    )
    if args.caso:
        carpetas = [p for p in carpetas if p.name in args.caso]
    resultados = [confrontar(p) for p in carpetas]
    for resultado in resultados:
        print(json.dumps(resultado, ensure_ascii=False))
    (BASE / "resumen_confrontacion.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
