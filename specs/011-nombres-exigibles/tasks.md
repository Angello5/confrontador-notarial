# Tasks: F16 · Nombres exigibles y domicilio por DNI

**Fuentes**: `spec.md`, `plan.md`. Solo datos ficticios (`9000xxxx`, nombres inventados).

## Phase 1 — pruebas rojas

- [ ] T001 Mención sin ficha y adjunto ausentes del borrador → sin `FALTA`; nombre de ancla y de minuta ausentes → `FALTA`; nombre del borrador igual a una mención → sin «no coincide» (FR-001, FR-002, `tests/test_personas.py`).
- [ ] T002 Domicilio en la cláusula del DNI con nombre mal escrito → sin aviso; ausente de todas las cláusulas → aviso (FR-004).
- [ ] T003 `confrontar_borrador` pasa los nombres exigibles (FR-005, `tests/test_expedientes_confrontacion.py`).
- [ ] T004 Paridad F13/F15: añadir la salida con nombres exigibles y anotar qué cambia.

## Phase 2 — implementación y entrega

- [ ] T005 `revisar(..., exigibles=None)`, `nombres_exigibles()` y domicilio por DNI (`nucleo/verificar.py`); llamada en `expedientes/services.py`.
- [ ] T006 Fixtures, suite con cobertura, Ruff, `check`, `makemigrations --check`, `git diff --check`; commits locales sin push.
- [ ] T007 **Medir SC-001, SC-002 (revisor, fuera del repositorio).**
