# Implementation Plan: F76 · Lectura rápida de escaneos en el servidor

**Branch**: `feat/f76-lectura-paralela` | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/057-lectura-paralela/spec.md`

## Summary

La lectura de escaneos pasa a usar OpenVINO como motor de ejecución de RapidOCR, con los mismos modelos ONNX, y reparte las páginas escaneadas de cada documento entre varios procesos de lectura. La cola toma primero borradores y minutas. La protección de los documentos largos ya existe desde F34 (bloqueo del proceso que lee) y no se toca. Todo se dimensiona para el Xeon Bronze 3204 del servidor (6 núcleos, sin Hyper-Threading): 3 procesos de 1 hilo por defecto, configurables por variables de entorno.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: Django, `rapidocr==3.10.0`, `onnxruntime==1.31.1`, PyMuPDF. Nueva: `openvino` (versión fijada con hashes en la implementación; medido con 2026.4.1).

**Storage**: PostgreSQL 17. Sin migraciones: no cambia ningún modelo.

**Testing**: `pytest` con fixtures ficticios; medición privada fuera del repositorio.

**Target Platform**: HPE ProLiant ML110 Gen10, Xeon Bronze 3204 (6 núcleos, 6 hilos, AVX-512, sin Turbo Boost), 64 GB, Windows Server 2019 Standard. El worker corre como tarea programada con una cuenta sin privilegios.

**Project Type**: monolito Django; el cambio vive en el adaptador de extracción y en la orquestación del worker.

**Performance Goals**: al menos el doble de páginas por minuto que la lectura actual, medido en el servidor (SC-001).

**Constraints**: texto y avisos de calidad idénticos a los de hoy (FR-002, FR-003); como máximo 3 núcleos y 6 GB con la configuración por defecto (SC-003); sin red en ejecución.

**Scale/Scope**: máximo 10 usuarios; kardex de 14 a 86 páginas, casi todas escaneadas.

## Constitution Check

| Principio | Cumplimiento |
|---|---|
| I. Determinismo | Mismos modelos, resolución y reglas de relectura. El texto debe salir idéntico; una diferencia bloquea la fase. El reparto entre procesos no altera el resultado: cada página se lee sola y el orden se reconstruye por índice. |
| II. Núcleo puro | El núcleo no cambia. El reparto de páginas vive en `adaptadores/extraccion.py`; el adaptador sigue sin importar Django. |
| III. Pruebas primero | Cada cambio empieza con su prueba: orden y texto idénticos, prioridad de la cola, arranque del worker y fallo de una página. |
| IV. Privacidad | Los procesos de lectura reciben la ruta del temporal y el número de página; no se escriben copias. El motor entra en la llave de la caché de texto. Los registros solo llevan identificadores y tiempos. |
| V. Simplicidad | Biblioteca estándar (`concurrent.futures`) para el reparto. Sin colas externas ni abstracciones nuevas. Una sola dependencia nueva, justificada abajo. |
| VI. Seguridad | Sin cambios de permisos. Todo corre dentro del servidor, con la cuenta de servicio. |
| VII. DevSecOps | `openvino` fijado con hashes y auditado con `pip-audit`. CI y Quality Gate sin excepciones. |
| VIII. Usabilidad | Sin pantallas nuevas; los estados visibles no cambian. |

Sin violaciones. Revisado de nuevo tras el diseño: sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/057-lectura-paralela/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/configuracion.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
adaptadores/extraccion.py        # motor configurable y reparto de páginas
expedientes/services.py          # prioridad en tomar_pendiente y métricas
expedientes/management/commands/procesar_documentos.py   # comprobación del motor al arrancar
requirements.in, requirements.txt                        # + openvino
scripts/medir_lectura_paralela.py                        # medición reproducible (FR-012)
tests/test_lectura_paralela.py                           # nuevo
tests/test_expedientes_worker.py                         # casos nuevos
specs/046-despliegue/quickstart.md                       # límites de recursos (FR-011)
docs/mediciones-ocr.md                                   # resultado en el servidor
```

**Structure Decision**: se mantiene el monolito. El adaptador decide cómo leer; `services.py` orquesta y guarda; el comando del worker solo arranca y comprueba.

## Complexity Tracking

| Complejidad | Por qué hace falta | Alternativa más simple descartada |
|---|---|---|
| Dependencia nueva `openvino` | Es la vía que más rinde con texto idéntico: 58 a 69 páginas por minuto frente a 8 a 33 del motor actual en la medición de desarrollo. El usuario la aprobó el 2026-11-16. | Solo repartir páginas con ONNX Runtime: menos ganancia y cifras inestables. |
| Procesos de lectura dentro del worker | El caso común es un solo PDF grande; varios workers por documento no lo aceleran. | Lanzar más copias del comando `procesar_documentos`. |
