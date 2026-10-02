"""Muestra privada antes/después; no mide precisión sin etiquetas humanas.

Selecciona hasta dos páginas PDF no vacías por caso (primera y última).
Textos y referencia quedan exclusivamente bajo expedientes_locales.
"""

import contextlib
import io
import json
import sys
import time
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from adaptadores import extraccion  # noqa: E402
from nucleo import verificar  # noqa: E402

BASE = ROOT / "expedientes_locales" / "auditoria-20261002"
OUT = BASE / "mejora_ocr"


def main():
    OUT.mkdir(exist_ok=True)
    inventario = json.loads((BASE / "resumen_ocr.json").read_text(encoding="utf-8"))
    referencia = []
    resultados = []
    for caso in inventario:
        nombre = caso["caso"]
        opciones = []
        for doc in caso["documentos"]:
            referencia.append(
                {
                    "caso": nombre,
                    "documento": doc["id"],
                    "paginas": doc["paginas"],
                    "estado": "pendiente_revision_notarial",
                    "anotaciones": [],
                }
            )
            if doc["formato"] != ".pdf":
                continue
            archivo = BASE / nombre / (doc["id"] + ".pdf")
            paginas = (
                archivo.with_suffix(".texto.txt")
                .read_text(encoding="utf-8")
                .split(extraccion.SEPARADOR_PAGINA)
            )
            opciones.extend((archivo, i, t) for i, t in enumerate(paginas) if t.strip())
        seleccionadas = opciones[:1] + (opciones[-1:] if len(opciones) > 1 else [])
        for archivo, i, anterior in seleccionadas:
            inicio = time.perf_counter()
            with pymupdf.open(archivo) as pdf:
                with contextlib.redirect_stderr(io.StringIO()):
                    informe = extraccion.ocr_informe(
                        pdf[i].get_pixmap(dpi=extraccion.DPI).tobytes("png")
                    )
            nuevo = informe["texto"]
            identificador = f"{nombre}-{archivo.stem}-p{i + 1}"
            (OUT / (identificador + ".json")).write_text(
                json.dumps(
                    {"anterior": anterior, "nuevo": informe},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            antes = verificar.catalogo({"ficticio.pdf": anterior})
            despues = verificar.catalogo({"ficticio.pdf": nuevo})
            fila = {
                "caso": nombre,
                "documento": archivo.stem,
                "pagina": i + 1,
                "texto_igual": anterior == nuevo,
                "caracteres_antes": len(anterior),
                "caracteres_despues": len(nuevo),
                "segundos": round(time.perf_counter() - inicio, 2),
                "requiere_revision": informe["requiere_revision"],
                "intentos": informe["intentos"],
                "campos": {
                    k: {
                        "retenidos": len(antes[k] & despues[k]),
                        "nuevos": len(despues[k] - antes[k]),
                        "ausentes": len(antes[k] - despues[k]),
                    }
                    for k in ("DNI", "NOMBRE", "PARTIDA", "MONTO")
                },
            }
            resultados.append(fila)
            print(
                json.dumps({k: v for k, v in fila.items() if k != "campos"}), flush=True
            )
    (OUT / "comparacion.json").write_text(
        json.dumps(resultados, indent=2), encoding="utf-8"
    )
    # Una repetición de la medición nunca sobrescribe el trabajo del revisor.
    destino = OUT / "referencia_pendiente.json"
    if not destino.exists():
        destino.write_text(
            json.dumps(
                {
                    "casos": referencia,
                    "campos_anotacion": [
                        "pagina",
                        "campo",
                        "sujeto",
                        "rol",
                        "bien",
                        "moneda",
                        "concepto",
                        "fecha_fuente",
                        "valor_observado",
                        "valor_esperado",
                        "tipo_error",
                        "validado_por_revisor",
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
