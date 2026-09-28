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
