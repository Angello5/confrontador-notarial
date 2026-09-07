"""Compara modelos sobre los defectos de prosa YA verificados del borrador.

  python3 bench_llm.py [modelo ...]

Verdad: lo que esta mal en el borrador y bien en Resultado/72156.docx.
"""
import sys
import time
from pathlib import Path

from extraer import leer
from revisor_llm import filtrar, consultar

BASE = Path(__file__).parent
# tokens de prosa mal escritos en el borrador y corregidos en la escritura final
VERDAD = {"OCTAO": "OCTAVO", "DECIO": "DECIMO", "MEIO": "MEDIO",
          "OCUPACIÒN": "OCUPACIÓN", "UIRBANIZACION": "URBANIZACION", "QUÉ": "QUE"}
MODELOS = sys.argv[1:] or ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.7-flash"]
CORRIDAS = 3

doc = leer(BASE / "Proyecto(borrador)" / "1785794688639_71168_malo2.docx")
fuentes = leer(BASE / "Cliente" / "1785794688252_DONACION_ACCIONES_Y_DERECHOS_-_KARIN.docx")

print(f"{'modelo':24} {'corrida':>7} {'crudos':>7} {'pasan':>6} {'aciertos':>9} {'ruido':>6} {'seg':>6}")
for modelo in MODELOS:
    encontrados = []
    for i in range(1, CORRIDAS + 1):
        t = time.perf_counter()
        try:
            crudos = consultar(doc, modelo)
        except Exception as e:
            print(f"{modelo:24} {i:>7}  ERROR {str(e)[:60]}")
            continue
        ok, fuera = filtrar(crudos, doc, fuentes.upper())
        hits = {v for v in VERDAD if any(v in h["encontrado"] for h in ok)}
        ruido = [h for h in ok if not any(v in h["encontrado"] for v in VERDAD)]
        encontrados.append(hits)
        print(f"{modelo:24} {i:>7} {len(crudos):>7} {len(ok):>6} "
              f"{len(hits)}/{len(VERDAD):<7} {len(ruido):>6} {time.perf_counter() - t:>6.1f}")
    if encontrados:
        estable = "sí" if all(h == encontrados[0] for h in encontrados) else "NO"
        union = set().union(*encontrados)
        print(f"{'':24} {'union':>7} {'':>7} {'':>6} {len(union)}/{len(VERDAD):<7} "
              f"  mismo resultado en las 3: {estable}")
        for v in sorted(set(VERDAD) - union):
            print(f"{'':24} nunca encontro: {v}")
    print()
