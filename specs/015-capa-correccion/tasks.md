# Tasks: F21 · Capa de corrección y documento corregido

**Fuentes**: `spec.md`, `plan.md`. Solo datos ficticios (`9000xxxx`, nombres inventados).

## Phase 1 — pruebas rojas

- [X] T001 Núcleo: carga útil desde «debe decir»; descarta idéntico, prefijo, FALTA, «no coincide», NUMERO_EN_LETRAS y sin fuente; ids estables; ocurrencias por orden (FR-001–FR-009, `tests/test_correccion.py`).
- [X] T002 Adaptador: reemplazo en la ocurrencia, entre fragmentos `w:t`, conteo de palabras antes/después (P-04), original intacto, no aplicadas (FR-010–FR-013).
- [X] T003 Servicio y vistas: sin `confirmado` nada (P-10), huella cambiada, exclusión, registro, descarga con permisos, CSRF, original conservado solo para borrador `.docx` y borrado al eliminar/suprimir (FR-014–FR-021).

## Phase 2 — implementación y entrega

- [X] T004 `nucleo/correccion.py` y `adaptadores/docx_corregido.py`.
- [X] T005 Ajuste, modelo, migración, servicio, vistas, plantilla, comando de supresión.
- [X] T006 Enmienda de la constitución 1.7.0 y roadmap.
- [X] T007 Fixtures, suite con cobertura, Ruff, `check`, `makemigrations --check`, `git diff --check`; commits locales sin push.

## Phase 3 — ronda 2: todas las apariciones (A.3)

- [ ] T008 Pruebas rojas: erróneo repetido 3 veces → 3 corregidas y resto intacto (conteo); «9000011» junto a «90000111» solo con límite de palabra; competencia → ninguna en el tramo; par repetido = una fila; conteo en la vista y en el registro (FR-008, FR-008a, SC-005).
- [ ] T009 Núcleo sin `ocurrencia`, adaptador `apariciones()`/`aplicar()` sobre todas las apariciones, campo `apariciones` (migración 0004), vista «N apariciones».
- [ ] T010 Verificaciones de T007; commit local sin push.
