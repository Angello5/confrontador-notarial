# Tasks: F28 · Código reutilizable tras archivar y marca configurable

**Fuentes**: `spec.md`, `plan.md`. Solo datos ficticios.

## Phase 1 — pruebas rojas

- [ ] T001 Crear con el código de un archivado → expediente nuevo con historial vacío; crear o editar con el código de un activo → error de formulario (FR-001, FR-002, FR-004).
- [ ] T002 Restaurar con código ocupado → mensaje, sin cambios (FR-003).
- [ ] T003 Marca con `override_settings(ERP_NOMBRE="Notaria Ficticia")`: sello «NF», nombre y `<title>` en base y login; por defecto «ERP Notarial» (FR-005, FR-006).

## Phase 2 — implementación y entrega

- [ ] T004 Restricción condicional + migración `0007`, formulario y vistas.
- [ ] T005 `ERP_NOMBRE`, context processor y plantillas; quickstart.
- [ ] T006 Fixtures, suite con cobertura, Ruff, `check`, `makemigrations --check`, `git diff --check`; commits locales sin push.
