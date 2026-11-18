"""F76: mide la lectura de escaneos por motor, procesos e hilos.

Uso, en el equipo donde se quiera medir (el servidor de la notaría):

    python scripts/medir_lectura_paralela.py --paginas 40
    python scripts/medir_lectura_paralela.py --carpeta D:\\muestra-privada --paginas 60

Sin `--carpeta` genera escaneos ficticios. Con ella lee los PDF de esa carpeta
(fuera del repositorio) y solo deja recuentos: nunca texto.

Cada configuración corre en un proceso nuevo, para que la memoria y los modelos
de una no cuenten en la siguiente. La primera es la referencia (motor anterior,
un proceso): el texto y los avisos de las demás se comparan con ella.

Salida, una línea por configuración:

    motor=<m> procesos=<n> hilos=<h> paginas_min=<x> memoria_gb=<y> \
texto_identico=<a>/<total> avisos_identicos=<b>/<total>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

# motor, procesos, hilos (0 = los del motor). La primera es la referencia.
CONFIGURACIONES = (
    ("onnxruntime", 1, 0),
    ("openvino", 1, 0),
    ("openvino", 2, 1),
    ("openvino", 3, 1),
    ("openvino", 2, 2),
    ("openvino", 3, 2),
    ("openvino", 6, 1),
    ("onnxruntime", 3, 1),
)
AVISOS = ("metodo", "motivos", "requiere_revision", "intentos", "transformacion")


def _pico_mb(_=None) -> float:
    """Memoria máxima de este proceso, sin dependencias nuevas."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class Contadores(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (nombre, ctypes.c_size_t)
                for nombre in (
                    "PeakWorkingSetSize",
                    "WorkingSetSize",
                    "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage",
                    "QuotaPeakNonPagedPoolUsage",
                    "QuotaNonPagedPoolUsage",
                    "PagefileUsage",
                    "PeakPagefileUsage",
                )
            ]

        contadores = Contadores()
        contadores.cb = ctypes.sizeof(contadores)
        nucleo = ctypes.WinDLL("kernel32", use_last_error=True)
        nucleo.GetCurrentProcess.restype = wintypes.HANDLE
        nucleo.K32GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(Contadores),
            wintypes.DWORD,
        ]
        nucleo.K32GetProcessMemoryInfo(
            nucleo.GetCurrentProcess(), ctypes.byref(contadores), contadores.cb
        )
        return contadores.PeakWorkingSetSize / 2**20
    import resource

    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def _huella(valor) -> str:
    return hashlib.sha256(
        json.dumps(valor, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def medir_una(rutas: list[str]) -> dict:
    """Lee los PDF con la configuración del entorno. Devuelve solo recuentos."""
    from adaptadores import extraccion

    extraccion.comprobar_motor()
    # Calienta: cada proceso de lectura carga su motor antes de medir.
    extraccion._pdf_informe(Path(rutas[0]))
    inicio = time.perf_counter()
    informes = [i for ruta in rutas for i in extraccion._pdf_informe(Path(ruta))]
    segundos = time.perf_counter() - inicio
    picos = [_pico_mb()]
    if extraccion.procesos() > 1:
        # Varias tandas para alcanzar a todos los procesos de lectura.
        tareas = [(i,) for i in range(extraccion.procesos() * 4)]
        picos.append(
            max(extraccion._en_grupo(_pico_mb, tareas)) * extraccion.procesos()
        )
    extraccion.cerrar_grupo()
    return {
        "paginas": len(informes),
        "segundos": segundos,
        "memoria_gb": sum(picos) / 1024,
        "textos": [_huella(i["texto"]) for i in informes],
        "avisos": [_huella({k: i.get(k) for k in AVISOS}) for i in informes],
    }


def _ficticios(carpeta: Path, paginas: int) -> list[str]:
    from medir_tiempos_ingesta import escaneo, pagina_ficticia, pdf_escaneado

    rutas = []
    por_archivo = 10
    for inicio in range(0, paginas, por_archivo):
        ruta = carpeta / f"ficticio-{inicio:03d}.pdf"
        pdf_escaneado(
            [
                escaneo(
                    pagina_ficticia(semilla, lineas=60)[0], dpi=200, semilla=semilla
                )
                for semilla in range(inicio, min(inicio + por_archivo, paginas))
            ],
            ruta,
        )
        rutas.append(str(ruta))
    return rutas


def _externos(carpeta: Path, paginas: int) -> list[str]:
    import pymupdf

    rutas, total = [], 0
    for ruta in sorted(carpeta.rglob("*.pdf")):
        with pymupdf.open(ruta) as doc:
            total += len(doc)
        rutas.append(str(ruta))
        if total >= paginas:
            break
    return rutas


def _configuraciones(texto: str):
    if not texto:
        return CONFIGURACIONES
    return tuple(
        (motor, int(procesos), int(hilos))
        for motor, procesos, hilos in (c.split(":") for c in texto.split(","))
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--paginas", type=int, default=20)
    parser.add_argument("--carpeta", type=Path, help="PDF propios, fuera del repo")
    parser.add_argument(
        "--configuraciones",
        default="",
        help="motor:procesos:hilos separados por comas; la primera es la referencia",
    )
    parser.add_argument("--una", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.una:
        # Proceso hijo: una sola configuración, ya fijada en el entorno.
        print(json.dumps(medir_una(json.loads(Path(args.una).read_text("utf-8")))))
        return 0

    with tempfile.TemporaryDirectory(prefix="f76-medicion-") as tmp:
        tmp = Path(tmp)
        rutas = (
            _externos(args.carpeta, args.paginas)
            if args.carpeta
            else _ficticios(tmp, args.paginas)
        )
        if not rutas:
            print("No hay PDF que medir.", file=sys.stderr)
            return 1
        lista = tmp / "rutas.json"
        lista.write_text(json.dumps(rutas), "utf-8")
        referencia = None
        for motor, procesos, hilos in _configuraciones(args.configuraciones):
            entorno = {
                **os.environ,
                "OCR_MOTOR": motor,
                "OCR_PROCESOS": str(procesos),
            }
            entorno.pop("OCR_HILOS", None)
            if hilos:
                entorno["OCR_HILOS"] = str(hilos)
            hijo = subprocess.run(  # noqa: S603 este mismo script, con argumentos propios
                [sys.executable, __file__, "--una", str(lista)],
                env=entorno,
                capture_output=True,
                text=True,
                check=False,
            )
            if hijo.returncode:
                error = (hijo.stderr.strip().splitlines() or ["sin detalle"])[-1]
                print(f"motor={motor} procesos={procesos} hilos={hilos} error={error}")
                continue
            dato = json.loads(hijo.stdout.strip().splitlines()[-1])
            referencia = referencia or dato
            total = dato["paginas"]
            iguales = lambda campo: sum(  # noqa: E731
                a == b for a, b in zip(dato[campo], referencia[campo])
            )
            print(
                f"motor={motor} procesos={procesos} hilos={hilos or 'motor'} "
                f"paginas_min={total / dato['segundos'] * 60:.1f} "
                f"memoria_gb={dato['memoria_gb']:.1f} "
                f"texto_identico={iguales('textos')}/{total} "
                f"avisos_identicos={iguales('avisos')}/{total}",
                flush=True,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
