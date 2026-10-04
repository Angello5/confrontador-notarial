# Implementation Plan: F32 · Vista del borrador con errores resaltados

**Branch**: `026-vista-borrador-resaltada` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/026-vista-borrador-resaltada/spec.md`

## Summary

La pantalla de resultado muestra las páginas del borrador como imagen, con un recuadro por observación
coloreado por severidad. Se reutiliza lo que ya existe: el original conservado de F21, LibreOffice
(`_soffice`) para convertirlo a PDF, PyMuPDF para dibujar la página y leer la posición de cada
palabra, y `correccion.coincidencias` para encontrar el valor observado. La ubicación sobre la página
es una función pura nueva del núcleo, que recibe segmentos de texto con su rectángulo y devuelve
rectángulos. Se añaden dos vistas GET con permisos: una devuelve en JSON las páginas y los recuadros,
y la otra devuelve la imagen PNG de una página. Alpine las consume en `confrontacion.html`.

**Entrega en dos tramos**:

- **Tramo A (US1 y US3, ya)**: borradores `.docx`, que ya se conservan con la constitución 1.7.0.
- **Tramo B (US2, bloqueado)**: borradores escaneados y demás formatos. Empieza solo cuando la
  constitución 1.8.0 esté aprobada e integrada. Ninguna tarea de este tramo conserva archivos
  antes de esa aprobación.

## Technical Context

**Language/Version**: Python 3.13 (CI); local 3.12 en `.venv`

**Primary Dependencies**: Django 5.2.17, PyMuPDF 1.28.2, LibreOffice headless (ya aprovisionado),
Alpine.js (ya vendorizado). Sin dependencias nuevas.

**Storage**: PostgreSQL (sin modelos ni migraciones nuevas). Original en
`EXPEDIENTES_ORIGINALES_DIR`. El PDF de vista, que es derivado, va como caché en
`EXPEDIENTES_TEMP_DIR`.

**Testing**: pytest. Funciones puras del núcleo con datos ficticios; vistas con cliente de Django y
`.docx` ficticio generado en el test.

**Target Platform**: servidor on-premise en la LAN de la notaría (Windows Server; F8 decide si es
nativo o VM)

**Project Type**: monolito Django (apps `expedientes`, `adaptadores`, `nucleo`)

**Performance Goals**: página visible en < 2 s cuando el PDF de vista ya está en caché. La primera
conversión con LibreOffice puede tardar hasta unos 10 s y la lista sigue usable mientras tanto.

**Constraints**: determinista; sin internet; sin rutas, nombres ni contenido en logs; imágenes con
`Cache-Control: no-store`

**Scale/Scope**: ≤ 10 usuarios; borradores de 5 a 60 páginas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| I. Determinismo, sin IA | Ubicación por igualdad normalizada (`coincidencias`). Misma entrada y misma versión de LibreOffice y PyMuPDF dan los mismos recuadros. Sin modelos. | ✅ |
| II. Núcleo puro | `marcas()` en `nucleo/correccion.py` (junto a `coincidencias`; el núcleo no importa entre sus módulos) recibe segmentos `(texto, x0, y0, x1, y1, linea)` y devuelve rectángulos; no importa Django, PyMuPDF ni archivos. La lectura de la página es un adaptador (`adaptadores/paginas.py`). Las vistas son delgadas. | ✅ |
| III. Tests primero | Cada función del núcleo y del adaptador empieza con un test que falla y usa solo datos ficticios. | ✅ |
| IV. Privacidad | Tramo A: solo usa el `.docx` ya conservado (1.7.0). El PDF de vista es un derivado temporal en `EXPEDIENTES_TEMP_DIR`: lo limpia `limpiar_temporales` a las 24 h y lo borra la supresión. Tramo B: **requiere la 1.8.0 aprobada**. | ✅ A / ⏸ B |
| V. Simplicidad | Sin modelos, sin API REST: dos vistas GET como `expediente_estado`. Sin abstracciones nuevas. | ✅ |
| VI. Seguridad | `login_required`, `_requiere_rol`, `_expediente_visible`; el borrador pertenece al expediente; SHA-256 verificado antes de convertir; sin rutas en respuestas ni logs. | ✅ |
| VII. DevSecOps | ruff, pytest, cobertura ≥ 80 % en código nuevo, Quality Gate. | ✅ |
| VIII. Usabilidad | Estados de carga, aviso de no disponible, teclado, foco visible, leyenda y doble codificación de la severidad. | ✅ |

**Re-check tras el diseño (Phase 1)**: sin violaciones nuevas. La Complexity Tracking queda vacía.

## Project Structure

### Documentation (this feature)

```text
specs/026-vista-borrador-resaltada/
├── spec.md
├── plan.md              # este archivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── vista-borrador.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
nucleo/
└── correccion.py                # + marcas(segmentos, valor) → rectángulos (puro)

adaptadores/
├── paginas.py                   # NUEVO: pdf_de_vista(original) vía _soffice; segmentos(pdf, n); png(pdf, n)
├── extraccion.py                # _soffice admite .docx (hoy solo LEGACY)
└── calidad_ocr.py               # Tramo B: ordenar_filas() extraída de resumir() para reutilizarla

expedientes/
├── services.py                  # vista_borrador(expediente, borrador, corrida); ruta_vista(); borrado en supresión
├── views.py                     # documento_vista (JSON) y documento_vista_pagina (PNG)
├── urls.py                      # .../documentos/<doc_id>/vista/ y .../vista/<n>/
└── management/commands/suprimir_texto_expediente.py   # borra también la caché de vista

templates/expedientes/
├── confrontacion.html           # panel "Borrador" con páginas y recuadros (Alpine)
└── _vista_borrador.html         # NUEVO: marcado del visor

static/css/erp.css               # .marca-pagina[data-sev=ALTA|MEDIA|BAJA], leyenda, zoom

tests/
├── test_ubicacion_pagina.py     # núcleo
├── test_paginas_adaptador.py    # .docx ficticio → PDF → segmentos (requiere soffice)
└── test_vista_borrador.py       # vistas: permisos, JSON, PNG, no disponible, supresión
```

**Structure Decision**: se respeta el monolito y la separación núcleo / adaptador / app que ya
existe. El código nuevo se reparte en una función del núcleo (`marcas` en `nucleo/correccion.py`), un módulo
(`adaptadores/paginas.py`), dos vistas, una plantilla parcial y CSS.

## Complexity Tracking

Sin violaciones que justificar.
