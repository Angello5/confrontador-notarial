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
- [X] T007 **Medir SC-001, SC-002 (revisor, fuera del repositorio).** Resultado 2026-09-27, solo recuentos: caso de referencia con errores intencionados 3/8 → 8/8 contra la lista oficial del propietario. En los 9 casos sin errores intencionados aparecen 2 observaciones nuevas, ambas DNI de 6 dígitos presentes de verdad en esos borradores; ningún falso positivo tras corregir los nombres de fuente con signos del OCR y las palabras numéricas de tres letras.
