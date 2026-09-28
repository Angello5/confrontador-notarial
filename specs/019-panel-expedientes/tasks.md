# Tasks: F25 · Panel de expedientes: abrir, editar y eliminar

**Fuentes**: `spec.md`, `plan.md`. Solo datos ficticios.

## Phase 1 — pruebas rojas

- [ ] T001 Botones Abrir/Editar/Eliminar en lista y detalle (FR-001, `tests/test_panel_expedientes.py`).
- [ ] T002 Editar: GET formulario, POST cambia código, código duplicado → error; otro usuario → 403; sin CSRF → 403 (FR-002, FR-003).
- [ ] T003 Eliminar: GET muestra el código; POST archiva; otro usuario → 403; sin CSRF → 403 (FR-004).
- [ ] T004 Archivado oculto en lista, inicio y métricas; detalle y carga → 404; manifiesto intacto (FR-005, SC-002).
- [ ] T005 Filtro «Archivados» y restaurar solo Administrador (FR-006).

## Phase 2 — implementación y entrega

- [ ] T006 Modelo + migración `0004`, servicio de visibilidad, vistas, URLs y plantillas.
- [ ] T007 Fixtures, suite con cobertura, Ruff, `check`, `makemigrations --check`, `git diff --check`; commits locales sin push.
