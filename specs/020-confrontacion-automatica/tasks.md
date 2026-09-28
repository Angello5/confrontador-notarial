# Tasks: F26 · Confrontación automática al terminar la carga

**Fuentes**: `spec.md`, `plan.md`. Solo datos ficticios (`9000xxxx`, nombres inventados).

## Phase 1 — pruebas rojas

- [ ] T001 Worker con todo LISTO → corrida AUTOMATICA con usuario que subió el borrador; segunda vuelta no duplica (FR-001, FR-003, SC-001).
- [ ] T002 Subir o eliminar una fuente → la siguiente vuelta reconfronta (SC-002).
- [ ] T003 Botón: «Confrontando…» gris mientras procesa o sin corrida; «Ver resultado» azul con corrida; «Volver a confrontar» registra MANUAL (FR-006).
- [ ] T004 Sondeo JSON: `resultado_listo` sin hallazgos ni rutas (FR-007, SC-004).
- [ ] T005 «Ver resultado» renderiza desde la corrida sin llamar al núcleo; permisos (FR-008, SC-003).
- [ ] T006 Fallo automático → corrida ERROR, sin reintento automático, botón de reintento manual (FR-009).

## Phase 2 — implementación y entrega

- [ ] T007 Modelo y migración; servicios; comando del worker.
- [ ] T008 Vista, URL y plantilla.
- [ ] T009 Fixtures, suite con cobertura, Ruff, `check`, `makemigrations --check`, `git diff --check`; commits locales sin push.
