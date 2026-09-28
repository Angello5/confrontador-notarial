# Tasks: F24 · Montos exigibles

**Fuentes**: `spec.md`, `plan.md`. Solo datos ficticios.

## Phase 1 — pruebas rojas

- [ ] T001 Monto de un recaudo ausente del borrador → sin `FALTA`; monto de la minuta ausente → `FALTA`; monto del borrador igual al de un recaudo → sin «no coincide»; monto alterado → «debe decir» (FR-001, FR-002, `tests/test_montos_exigibles.py`).
- [ ] T002 Sin `montos_exigibles` la salida es la de siempre (FR-004).
- [ ] T003 `confrontar_borrador` solo exige los montos de la minuta (FR-004, `tests/test_expedientes_confrontacion.py`).

## Phase 2 — implementación y entrega

- [ ] T004 `revisar(..., montos_exigibles=None)` y `montos_exigibles()` (`nucleo/verificar.py`); llamada en `expedientes/services.py`.
- [ ] T005 Fixtures, suite con cobertura, Ruff, `check`, `makemigrations --check`, `git diff --check`; commits locales sin push.
- [ ] T006 **Medir SC-001 (revisor, fuera del repositorio).**
