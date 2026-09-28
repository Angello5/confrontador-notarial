# Tasks: F27 · Montos por posición, con moneda y concepto

**Fuentes**: `spec.md`, `plan.md`. Solo datos ficticios.

## Phase 1 — pruebas rojas

- [X] T001 Moneda: US$ alterado, S/ 100 frente a US$ 100, `S/.` y sufijo `SOLES`/`DOLARES` (FR-001, `tests/test_montos_contexto.py`).
- [X] T002 Posición: cuota intercambiada, precio sustituido por otro importe válido, cronograma idéntico sin observaciones, párrafo sin par con la regla actual (FR-002, FR-003).
- [X] T003 `services`: `concepto` y `fuente` en el dict (FR-004).

## Phase 2 — implementación y entrega

- [X] T004 `nucleo/verificar.py` y `expedientes/services.py`.
- [X] T005 Fixtures, suite con cobertura, Ruff, `check`, `makemigrations --check`, `git diff --check`; commits locales sin push.
- [ ] T006 **Medir SC-001 (revisor, fuera del repositorio).**

## Phase 3 — ronda 2: filas de tabla en .docx

- [ ] T007 Rojo: `_docx` con tabla (fila = línea, celdas con dos espacios, párrafos de celda con espacio, tabla anidada aplanada, fuera de tabla igual); cronograma de 12 filas en borrador y minuta `.docx` con la fila 5 sustituida por el importe de la fila 9 → una MONTO; idéntico → ninguna (FR-006).
- [ ] T008 Rojo: `version_extractor()` cambia con `_FORMATO_TEXTO`; `reextraer_expediente` encola con archivo y no toca sin archivo (FR-007).
- [ ] T009 Implementación y verificaciones de T005.
