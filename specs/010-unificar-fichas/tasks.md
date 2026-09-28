# Tasks: F15 · Una persona por DNI entre fichas oficiales

**Fuentes**: `spec.md`, `plan.md`. `[X]` indica evidencia ya producida.
T007 queda para el revisor. Solo datos ficticios (`9000xxxx`, nombres
inventados).

## Phase 1 — paridad (antes de tocar el núcleo)

- [ ] T001 Confirmar en verde la paridad literal de `revisar()`, `correspondencia()`, `diagnostico()` y `revisar_parrafos()` sobre fixtures ficticios con el código actual (SC-004, `tests/test_personas.py`).

## Phase 2 — pruebas rojas (`tests/test_personas.py`)

- [ ] T002 RENIEC + biométrica, mismo DNI, espacio leído como letra → 1 ancla `CONFIRMADA`, nombre RENIEC, variante como adjunto con procedencia, ambos nombres en `cat["NOMBRE"]` (FR-001..FR-004, FR-006).
- [ ] T003 Mismo DNI, 2 ediciones → `CONFIRMADA`; 3 o más → `REVISION_MANUAL`; nombre biométrico truncado → `REVISION_MANUAL` con nombre RENIEC (FR-004).
- [ ] T004 Dos RENIEC mismo DNI y nombres distintos → nombre de la emisión más reciente; sin fecha, la primera por página. DNI distinto y mismo nombre → 2 anclas. Conflicto F12 sin cambios (FR-002, FR-005).
- [ ] T005 Ajustar las pruebas F13 que esperaban dos anclas con el mismo documento.

## Phase 3 — implementación y entrega

- [ ] T006 `unificar_personas(personas, tipos)` para anclas y `_pegar()` con adjuntos previos (`nucleo/verificar.py`); fixtures, suite con cobertura, Ruff, `check`, `makemigrations --check`, `git diff --check`.
- [ ] T007 **Medir SC-001..SC-003 (revisor, fuera del repositorio y de CI).**
- [ ] T008 Actualizar `spec.md` si la implementación cambió comportamiento no descrito; commits locales sin push ni PR.
