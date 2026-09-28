# Tasks: F20 · Manifiesto de auditoría

**Fuentes**: `spec.md`, `plan.md`. Solo datos ficticios (`9000xxxx`, nombres inventados).

## Phase 1 — pruebas rojas

- [X] T001 Catálogo: versión, todas las reglas con severidad válida, campo desconocido → por defecto (FR-001, FR-002).
- [X] T002 Confrontar desde la vista crea una corrida con hashes, versiones, usuario, fecha, huella; observaciones con severidad (FR-002–FR-004, SC-002).
- [X] T003 Tres corridas idénticas → misma huella (SC-001).
- [X] T004 Inmutabilidad de `Corrida` y `DecisionCorreccion` (FR-005, FR-006).
- [X] T005 `reconstruir_corrida`: CONFORME, texto suprimido, catálogo distinto (FR-007, SC-003).
- [X] T006 Fallo del núcleo → corrida ERROR sin hallazgos, documentos intactos (FR-009, SC-004).
- [X] T007 Historial y detalle: permisos, recuentos por severidad; sondeo JSON sin corridas (FR-008, FR-010).

## Phase 2 — implementación y entrega

- [X] T008 Catálogo TOML, severidad y corrida en `services.py`; modelos y migración.
- [X] T009 Comando `reconstruir_corrida`.
- [X] T010 Vistas, URLs y plantillas.
- [X] T011 Fixtures, suite con cobertura, Ruff, `check`, `makemigrations --check`, `git diff --check`; commits locales sin push.
