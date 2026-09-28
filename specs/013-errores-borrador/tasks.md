# Tasks: F19 · Errores del borrador fuera de la comparecencia

**Fuentes**: `spec.md`, `plan.md`. Solo datos ficticios (`9000xxxx`, nombres inventados).

## Phase 1 — pruebas rojas

- [X] T001 DNI con 7 y 9 dígitos tras rótulo → `[DNI]` con el más cercano o «no coincide»; número suelto de 7 dígitos y DNI correcto → nada (FR-001, FR-002, `tests/test_errores_borrador.py`).
- [X] T002 Nombre mal escrito tras «EN REPRESENTACION DE» → `[NOMBRE]`; nombre idéntico, dos personas parecidas con una exacta y ventana ya observada → nada (FR-003, FR-004).
- [X] T003 Letras y cifra distintas o palabra mal escrita → `[NUMERO_EN_LETRAS]`; coincidentes, importe `Y 00/100 (1,500.00)` y «PRIMERA (1)» → nada (FR-005, FR-006).
- [X] T004 Paridad F13/F15: salida literal de `revisar()` sin cambios (SC-003, pruebas existentes).

## Phase 2 — implementación y entrega

- [X] T005 Detectores en `revisar()` (`nucleo/verificar.py`); el adaptador de `services.py` los interpreta sin cambios (prueba de adaptación).
- [X] T006 Fixtures, suite con cobertura, Ruff, `check`, `makemigrations --check`, `git diff --check`; commits locales sin push.
- [ ] T007 **Medir SC-001, SC-002 (revisor, fuera del repositorio).**
