# Tareas · F33

Pruebas primero (constitución III): cada prueba se escribe y se ve fallar antes de su implementación. Solo datos ficticios.

## Fase 1 · Preparación

- [x] T001 Incorporar el script y las mediciones previas de tiempos en `scripts/medir_tiempos_ingesta.py`, `docs/ocr-tiempos-2026-10-02.md` y `docs/ocr-tiempos.json`, y registrar F33 en `docs/roadmap.md`.
- [x] T002 Guardar una copia del extractor de `main` fuera del repositorio (`.venv/ocr-tiempos/extraccion_antes.py`) para medir antes/después.

## Fase 2 · Base

- [x] T003 Subir `VERSION` de 2 a 3 en `adaptadores/calidad_ocr.py` con su prueba de identidad en `tests/test_calidad_ocr.py` (FR-008).

## Fase 3 · US1 · Escaneos más rápidos con el mismo texto (P1)

Prueba independiente: mismo texto por página que la versión anterior, menos tiempo.

- [x] T004 [US1] Pruebas que fallan en `tests/test_calidad_ocr.py`: el motor se crea con `EngineConfig.onnxruntime.enable_cpu_mem_arena` verdadero; `_pdf_informe` entrega al motor una matriz `numpy` BGR (alto × ancho × 3), no bytes PNG; `ocr_informe` acepta esa matriz y sus giros también llegan como matriz (FR-001).
- [x] T005 [US1] Implementar la reserva de memoria en `_ocr` y la entrada en memoria en `_pdf_informe` y `ocr_informe` de `adaptadores/extraccion.py`, sin cambiar 200 dpi ni modelos (FR-001).
- [x] T006 [US1] Comprobar con el extractor previo (T002) que el texto de los PDF ficticios de `scripts/medir_tiempos_ingesta.py` es idéntico página a página (FR-002).

## Fase 4 · US2 · Páginas giradas (P1)

Prueba independiente: página al revés con 2 lecturas y sin aviso; página de lado con líneas en orden.

- [x] T007 [P] [US2] Prueba que falla en `tests/test_calidad_ocr.py`: `calidad_ocr.horizontal` devuelve la proporción de cajas más anchas que altas y 0 sin cajas.
- [x] T008 [P] [US2] Prueba que falla en `tests/test_calidad_ocr.py`: lectura original sin texto y giro de 180° legible → 2 lecturas, sin `lecturas_divergentes`, sin revisión (FR-003, FR-004).
- [x] T009 [P] [US2] Prueba que falla en `tests/test_calidad_ocr.py`: giro de 180° con cajas verticales y giro de 270° con cajas horizontales e igual puntuación → gana 270° (FR-005).
- [x] T010 [US2] Prueba de no regresión en `tests/test_calidad_ocr.py`: dos lecturas extensas con números distintos mantienen `lecturas_divergentes` (F31).
- [x] T011 [US2] Implementar `horizontal` en `adaptadores/calidad_ocr.py` y la comparación ponderada `puntuacion × (0,5 + horizontal)`, la exclusión de lecturas vacías o escasas y la parada solo con lectura sin revisión y más del 80 % de cajas horizontales en `ocr_informe` (FR-003 a FR-005).

## Fase 5 · US3 · Hojas totalmente blancas (P2)

Prueba independiente: hoja blanca sin lecturas; hoja con una línea corta se lee.

- [x] T012 [US3] Ajustar en `tests/test_calidad_ocr.py` `test_reintentos_acotados_y_pagina_vacia` (hoja blanca: 0 lecturas) y añadir pruebas que fallan: hoja blanca con ruido ≤ 0,001 % de píxeles oscuros → 0 lecturas, `pagina_casi_vacia`, revisión; hoja con una marca de 60 píxeles oscuros en A4 a 200 dpi → se lee (FR-006).
- [x] T013 [US3] Implementar la comprobación previa en `ocr_informe` de `adaptadores/extraccion.py` con el criterio de F31 (gris < 200) y umbral 0,001 %; si la imagen no se puede abrir, se omite la comprobación y se llama al motor como hoy (FR-006).

## Fase 6 · US4 · Conversión de formatos antiguos (P2)

Prueba independiente: dos conversiones en el mismo proceso usan el mismo perfil y el texto no cambia.

- [x] T014 [US4] Pruebas que fallan en `test_extraer.py` con `subprocess.run` simulado: dos conversiones usan el mismo `-env:UserInstallation` bajo `CACHE` con el pid del proceso; tras un fallo el perfil se borra y la siguiente conversión crea otro; nada queda en el directorio temporal (FR-007).
- [x] T015 [US4] Implementar el perfil por proceso en `_soffice` de `adaptadores/extraccion.py`, con borrado al salir del proceso (FR-007).

## Fase 7 · Cierre

- [x] T016 Ejecutar `scripts/medir_tiempos_ingesta.py --solo casos --repeticiones 2` (primera y segunda conversión del `.rtf` por separado) y la muestra privada antes/después; registrar solo agregados en `docs/ocr-tiempos-2026-10-02.md` (SC-001 a SC-005).
- [x] T017 Suite completa con cobertura, Ruff, `manage.py check`, `makemigrations --check` y dependencias sin cambios (FR-009); dejar indicado en el PR ejecutar `-m local_reference` donde exista el expediente de referencia; actualizar `spec.md` (estado) y marcar tareas (SC-006).

## Dependencias

T001–T003 → US1 (T004–T006) → US2 (T007–T011) y US3 (T012–T013), que tocan la misma función y se hacen en serie → US4 (T014–T015), independiente del OCR → T016–T017. Paralelizables: T007, T008 y T009 (pruebas en bloques distintos del mismo archivo, sin dependencia entre sí).

## Estrategia

MVP: US1 (−18 % medido en páginas reales, sin cambiar texto). Luego US2, que corrige exactitud además de tiempo; US3 y US4 son ahorros menores e independientes.

Verificación local (2026-10-03, Windows, Python 3.12): 604 pruebas Python aprobadas y 3 omitidas por el entorno; cobertura 93 %; 5 pruebas Node; Ruff, `manage.py check` y `makemigrations --check` sin cambios; dependencias intactas. Muestra privada: 12/12 páginas con texto idéntico y −20 % de tiempo. Pendientes: CI con Python 3.13, Quality Gate y `-m local_reference` donde exista el expediente de referencia.
