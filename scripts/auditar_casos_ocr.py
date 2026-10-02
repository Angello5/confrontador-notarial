"""Ejecuta el adaptador real sobre los casos privados ya aislados.

Guarda texto extraído únicamente en expedientes_locales/auditoria-20261002.
La salida estándar contiene solo conteos y clases de fallo, sin contenido.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from adaptadores import extraccion  # noqa: E402


DESTINO = ROOT / "expedientes_locales" / "auditoria-20261002"


def main():
    extraccion.CACHE = DESTINO / "cache"
    informe = []
    for carpeta in sorted(
        p
        for p in DESTINO.iterdir()
        if p.is_dir() and p.name != "deps" and p.name != "cache"
    ):
        documentos = []
        for ruta in sorted(carpeta.iterdir()):
            if (
                not re.fullmatch(r"D\d{3}", ruta.stem)
                or ruta.suffix.lower() not in extraccion.DOCS
            ):
                continue
            registro = {"id": ruta.stem, "formato": ruta.suffix.lower()}
            try:
                with contextlib.redirect_stderr(io.StringIO()):
                    paginas = extraccion.leer_paginas(ruta)
                texto = extraccion.SEPARADOR_PAGINA.join(paginas)
                (carpeta / f"{ruta.stem}.texto.txt").write_text(texto, encoding="utf-8")
                registro.update(
                    {
                        "estado": "leido",
                        "paginas": len(paginas),
                        "paginas_con_texto": sum(bool(p.strip()) for p in paginas),
                        "caracteres": len(texto),
                    }
                )
            except Exception as error:
                # Las excepciones de lectores pueden citar texto/rutas privados.
                registro.update({"estado": "error", "tipo_error": type(error).__name__})
            documentos.append(registro)
        informe.append({"caso": carpeta.name, "documentos": documentos})
        print(
            json.dumps(
                {
                    "caso": carpeta.name,
                    "estados": Counter(d["estado"] for d in documentos),
                    "pdf_paginas": sum(
                        d.get("paginas", 0)
                        for d in documentos
                        if d["formato"] == ".pdf"
                    ),
                    "pdf_paginas_con_texto": sum(
                        d.get("paginas_con_texto", 0)
                        for d in documentos
                        if d["formato"] == ".pdf"
                    ),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        (DESTINO / "resumen_ocr.json").write_text(
            json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
