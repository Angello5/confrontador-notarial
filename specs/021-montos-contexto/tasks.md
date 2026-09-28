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
