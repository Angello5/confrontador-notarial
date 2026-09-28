# Tasks: F16 · Nombres exigibles y domicilio por DNI

**Fuentes**: `spec.md`, `plan.md`. Solo datos ficticios (`9000xxxx`, nombres inventados).

## Phase 1 — pruebas rojas

- [X] T001 Mención sin ficha y adjunto ausentes del borrador → sin `FALTA`; nombre de ancla y de minuta ausentes → `FALTA`; nombre del borrador igual a una mención → sin «no coincide» (FR-001, FR-002, `tests/test_personas.py`).
- [X] T002 Domicilio en la cláusula del DNI con nombre mal escrito → sin aviso; ausente de todas las cláusulas → aviso (FR-004).
- [X] T003 `confrontar_borrador` pasa los nombres exigibles (FR-005, `tests/test_expedientes_confrontacion.py`).
- [X] T004 Paridad F13/F15: añadida la salida con nombres exigibles. Legajo F13: idéntica (sus 4 FALTA son de anclas o minuta). Fichas duplicadas F15: desaparece `[NOMBRE] FALTA: «OLGAIMIRELA TARANCO VELIZ»` (variante adjunta). Sin `exigibles`, ambas salidas literales siguen iguales.

## Phase 2 — implementación y entrega

- [X] T005 `revisar(..., exigibles=None)`, `nombres_exigibles()` y domicilio por DNI (`nucleo/verificar.py`); llamada en `expedientes/services.py`.
- [X] T006 Fixtures, suite con cobertura, Ruff, `check`, `makemigrations --check`, `git diff --check`; commits locales sin push.
- [ ] T007 **Medir SC-001, SC-002 (revisor, fuera del repositorio).**
