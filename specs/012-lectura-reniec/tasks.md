# Tasks: F18 · Lectura de fichas RENIEC escaneadas

**Fuentes**: `spec.md`, `plan.md`. `[X]` indica evidencia ya producida.
T006 queda para el revisor. Solo datos ficticios.

## Phase 1 — paridad

- [X] T001 Confirmar en verde la paridad literal de `revisar()`, `correspondencia()`, `diagnostico()` y `revisar_parrafos()` sobre los fixtures ficticios (SC-004, `tests/test_personas.py`).

## Phase 2 — pruebas rojas (`tests/test_personas.py`)

- [X] T002 Fecha con punto o espacio en el año se lee; ruido no numérico sigue sin leerse (FR-001).
- [X] T003 Valor en la línea siguiente para estado civil, fecha y dirección; negativos: línea siguiente que es otro rótulo y dirección sin dígito ni vía (FR-002).
- [X] T004 Nombre, paterno o materno con hora o vacío toma la línea siguiente alfabética; negativo: la línea siguiente es rótulo (FR-003).
- [X] T005 RENIEC sin nombre con ancla del mismo documento aporta sus campos con procedencia y emisión; sin ancla no cambia nada (FR-004).

## Phase 3 — implementación y entrega

- [ ] T006 **Medir SC-001..SC-003 (revisor, fuera del repositorio y de CI).**
- [X] T007 Implementar en `nucleo/verificar.py`; fixtures, suite con cobertura, Ruff, `check`, `makemigrations --check`, `git diff --check`; commits locales sin push ni PR.
