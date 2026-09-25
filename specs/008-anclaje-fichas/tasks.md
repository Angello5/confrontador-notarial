# Tasks: F13 · Anclaje por ficha oficial

**Fuentes**: `spec.md`, `research.md`, `plan.md`, `contracts/ui.md`.
`[X]` indica evidencia ya producida; nada de implementación está marcado.
Todas las pruebas usan datos ficticios (`9000xxxx`, nombres inventados).

## Phase 1 — decisiones documentales

- [X] T001 Fijar ancla = registro completo de página RENIEC/BIOMETRICA; fichas incompletas pasan a mención (research D1).
- [X] T002 Fijar representación: `adjuntos`/`conyuge`/`procedencia_conyuge` en `Persona` y `Catalogo.menciones` (research D2, D3).
- [X] T003 Fijar regla de pegado por documento único o clave de nombre única (research D4).
- [X] T004 Fijar `comparar_personas()` con titular ancla y pertenencia contra `fuente["DNI"]` (research D8).
- [ ] T005 Obtener respuesta del propietario a las dos `[NEEDS CLARIFICATION]` del cónyuge (research); hasta entonces se implementa el defecto propuesto.

## Phase 2 — paridad y contrato (antes de tocar el núcleo)

- [ ] T006 Prueba de paridad: salida literal de `revisar()`, `correspondencia()`, `diagnostico()` y `revisar_parrafos()` sobre los fixtures ficticios, capturada con el código actual; debe seguir verde al final (SC-005, `tests/test_personas.py`).
- [ ] T007 Prueba roja: `Persona` acepta 3/4 posicionales y los tres campos nuevos con defecto `None`; `Catalogo(personas)` sigue funcionando y `menciones` vale `()` (`tests/test_personas.py`).
- [ ] T008 Ampliar `Persona` al final y `Catalogo` con `menciones`; proyección `NOMBRE`/`DNI` desde anclas, adjuntos y menciones, con cónyuges (`nucleo/verificar.py`).

## Phase 3 — anclas y pegado (US FR-001..FR-005)

- [ ] T009 Pruebas rojas: prosa sola → 0 personas y 1 mención `SIN_FICHA`; RENIEC + biométrica del mismo documento y nombre → 1 ancla (FR-001, FR-005).
- [ ] T010 Pruebas rojas: prosa con documento de un ancla y nombre distinto → adjunto, ancla `CONFIRMADA`, ambos nombres en `cat["NOMBRE"]` (FR-002, FR-004, FR-008).
- [ ] T011 Pruebas rojas: nombre solo, igual a un ancla → adjunto; igual a dos anclas homónimas → mención; documento sin ancla con nombre de un ancla → mención, nunca adjunto (FR-003, research D4.3).
- [ ] T012 Pruebas rojas: dos anclas con documento distinto y mismo nombre → dos anclas; mismo documento y nombre distinto → `REVISION_MANUAL` en ambas; RENIEC con emisiones distintas → gana la más reciente (FR-004, FR-005, F12).
- [ ] T013 Prueba roja: ficha RENIEC sin documento legible → mención, no ancla (research D1, SC-002/SC-003).
- [ ] T014 Implementar en `catalogo()` la separación ancla/resto, `unificar_personas()` de anclas y el pegado; menciones deduplicadas con estado `SIN_FICHA` (`nucleo/verificar.py`).

## Phase 4 — cónyuge (FR-006)

- [ ] T015 Pruebas rojas: declaración jurada ficticia con declarante, documento y cónyuge → el declarante se pega por documento al ancla y el ancla lleva `conyuge` con su procedencia; el cónyuge no es persona ni mención; su nombre sigue en `cat["NOMBRE"]`.
- [ ] T016 Pruebas rojas: declarante sin documento pegado por nombre único; declarante sin ancla → mención con cónyuge; dos menciones del mismo declarante con cónyuges distintos no se fusionan.
- [ ] T017 Implementar extracción del cónyuge fuera de la lista de nombres en `_personas_de_pagina()` (bloque y líneas) y su tratamiento en `unificar_personas()` (`nucleo/verificar.py`).

## Phase 5 — comparación de personas

- [ ] T018 Reescribir con fichas ficticias las pruebas F11 de documento cruzado; añadir: comparecientes sin ficha intercambiados → sin `DOCUMENTO_CRUZADO` (Clarification); documento en la minuta sin ficha → sin `DOCUMENTO_SIN_TITULAR`; documento ausente de todas las fuentes → `DOCUMENTO_SIN_TITULAR`.
- [ ] T019 Adaptar `comparar_personas()` (research D8) (`nucleo/verificar.py`).

## Phase 6 — tabla de extracción (FR-007)

- [ ] T020 Pruebas: `_resumen_extraccion()` separa `personas` (anclas con cónyuge y adjuntos legibles) y `menciones`, global y por documento; nombre de archivo sin ruta (`tests/test_expedientes_confrontacion.py`).
- [ ] T021 Pruebas HTML: tablas «Personas con ficha» y «Menciones sin ficha», textos de ayuda, ausencias explícitas, escape; sondeo JSON sin campos nuevos (`tests/test_expedientes_confrontacion_ui.py`).
- [ ] T022 Implementar `_personas_legibles(personas)`, estado «Sin ficha» y la plantilla según `contracts/ui.md` (`expedientes/services.py`, `templates/expedientes/confrontacion.html`).

## Phase 7 — verificación, medición y entrega

- [ ] T023 `python scripts/generar_fixtures.py`, suite con cobertura, Ruff check/format, Django `check`, `makemigrations --check`, `git diff --check`, revisión del diff por privacidad (SC-006).
- [ ] T024 **Medir antes/después (ejecuta el revisor, fuera del repositorio y fuera de CI).** Con el mismo guion privado sobre los mismos 10 expedientes (369 páginas), primero en el commit base `9591ed0` y después en el commit de F13. Registrar solo recuentos, nunca datos:

  | Medida | Antes (spec) | Meta después |
  |---|---:|---:|
  | Personas confirmadas desde fichas (SC-001) | 49 | ≥ 49 |
  | Registros con nombre sin documento presentados como persona (SC-002) | 47 | 0 |
  | Registros con documento sin nombre presentados como persona (SC-003) | 33 | 0 |
  | Marcas de revisión manual, todas entre anclas (SC-004) | 64 | ≤ 6 |

  Además, medición `local_reference` (`-o addopts= -m local_reference --tb=no`) del expediente de referencia: 8 de 8 errores y 0 falsos positivos, sin retroceso (Constitución II/III). Si el «antes» no reproduce 49/47/33/64, se detiene y se informa: el guion o la base cambiaron.
- [ ] T025 Actualizar `spec.md` solo si la implementación obliga a cambiar comportamiento; commit local en `feature/f13-anclaje-fichas`, sin push ni PR.
