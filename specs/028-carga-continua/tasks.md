# Tasks · F34

## Setup
- [x] T001 Especificar y aclarar alcance aprobado en specs/028-carga-continua/spec.md.
- [x] T002 Investigar y diseñar contratos y datos en specs/028-carga-continua/plan.md.
- [x] T003 Preparar Python 3.13 y PostgreSQL aislado; evidencia en specs/028-carga-continua/quickstart.md. (Local: PostgreSQL aislado y Python 3.12; Python 3.13 lo valida CI en el PR.)

## US1 · Carga continua
- [x] T004 [US1] Tests de carga JSON y errores parciales en tests/test_carga_continua.py (FR-001/002).
- [x] T005 [US1] Respuesta JSON y cola de transferencias en expedientes/views.py y static/js/carga-expediente.js; interfaz en templates/expedientes/detalle.html (FR-001/002/009).

## US2 · Solicitudes
- [x] T006 [US2] Tests de idempotencia, cancelación, entradas cambiadas y atribución en tests/test_carga_continua.py (FR-003/004/005/006).
- [x] T007 [US2] Modelo, migración y servicios de solicitud en expedientes/models.py y expedientes/solicitudes.py; endpoints en expedientes/views.py y urls.py (FR-003/004/005/006).
- [x] T008 [US2] Intercalar procesamiento y preparar visor en expedientes/management/commands/procesar_documentos.py y expedientes/services.py (FR-007).

## US3 · Revisión visual
- [x] T009 [US3] Simplificar templates/expedientes/confrontacion.html, calidad y CSS; propuesta desde marca y alcance de apariciones (FR-009/010/011).
- [x] T010 [US3] Verificar UI y DOCX ficticios, original intacto, en tests/test_correccion_expedientes.py y navegador (FR-011).

## US4 · Concurrencia y medición
- [x] T011 [US4] Tests concurrentes PostgreSQL en tests/test_procesamiento_concurrente.py (FR-008).
- [x] T012 [US4] Locks de sesión en expedientes/bloqueos.py, recuperación segura, caché exclusiva y preview protegido en expedientes/services.py (FR-008).
- [x] T013 [US4] Duraciones sin datos personales y guía de benchmark en expedientes/services.py y specs/028-carga-continua/quickstart.md (FR-012).

## Verificación
- [x] T014 Tests completos, Ruff y checks Django; registrar evidencia en docs/carga-continua-2026-10-03.md (SC-001/006).
- [x] T015 Revisión de seguridad, permisos y regresiones; coherencia de specs F26/F32 y F34.
- [ ] T016 Integración por PR y CI/Quality Gate en checkout Git (bloqueo de entorno documentado).

## Dependencias y estrategia
T001→T002→T003; pruebas antes de cada cambio. T004/T006/T011 independientes; implementación secuencial para no competir sobre servicios. US1 primero, luego US2 y concurrencia, luego US3 y validación conjunta. No se despliega sin T016. Pruebas independientes por historia descritas en spec.md y quickstart.md.
