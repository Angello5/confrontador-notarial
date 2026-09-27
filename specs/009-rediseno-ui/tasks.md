# Tasks: F14 · Rediseño de interfaz

**Fuentes**: `spec.md`, `plan.md`, `contracts/ui.md`. `[X]` indica evidencia
ya producida. Todas las pruebas usan datos ficticios (`usuario_ficticio`,
`EXP-FICTICIO-…`).

## Phase 1 — base

- [ ] T001 `static/css/erp.css` con tokens como variables y redefinición de variables Bootstrap/AdminLTE; test de que se sirve localmente y lo cargan base y login (FR-002, SC-004).
- [ ] T002 Tests rojos del shell: marca, secciones por rol, «Usuarios y permisos» solo administrador, ítem activo con `aria-current` en lista/detalle, pie con usuario y rol, avatar, ☰ con `aria-expanded`; pendiente de cambio de clave sin shell (`tests/test_shell.py`).
- [ ] T003 Implementar el shell y la cabecera de página en `templates/core/base.html`; mover migas de cada pantalla al bloque `breadcrumb`.

## Phase 2 — fragmentos

- [ ] T004 `templates/core/_chip.html`, `_metrica.html`, `_riel.html`, `_zona_arrastre.html` según `contracts/ui.md`.

## Phase 3 — Inicio (US2, FR-004)

- [ ] T005 Tests rojos: métricas con expedientes ficticios en los cuatro estados; visibilidad (un usuario no cuenta los de otro, el administrador sí); cinco últimos; vacío con enlace; variante administrador; contexto sin texto/hash/ruta (`tests/test_shell.py`).
- [ ] T006 `expedientes_con_resumen()` en `expedientes/services.py`, usada por la lista y por `core.views.home`; plantilla `core/home.html`.

## Phase 4 — Expedientes, expediente y resultado (US3–US5)

- [ ] T007 Tests rojos: chip por estado en la lista; formulario con error visible; paso del riel por estado (vacío, falta minuta, falta borrador, procesando, listo); paneles y línea de privacidad (`tests/test_expedientes_ui.py`).
- [ ] T008 Plantillas `expedientes/lista.html`, `detalle.html`, `_zona_carga.html`.
- [ ] T009 Tests: métricas de Personas/Regla/Ortografía y cabecera del resultado; estados de aviso intactos (`tests/test_expedientes_confrontacion_ui.py`).
- [ ] T010 Plantilla `expedientes/confrontacion.html`.

## Phase 5 — ingreso y transversal (US6, FR-009)

- [ ] T011 Login con marca sobre navy y tarjeta blanca; cambio de clave con la nueva cabecera.
- [ ] T012 Test: ninguna plantilla contiene «IA»/«AI» como palabra.

## Phase 6 — verificación y entrega

- [ ] T013 `python manage.py check`, `makemigrations --check`, Ruff check/format, suite con cobertura (código nuevo ≥ 80 %), `git diff --check`, revisión del diff por datos reales.
- [ ] T014 Render real en `127.0.0.1:8001` de las seis pantallas a 1440 y 390 px; desviaciones del diseño anotadas en este archivo.
- [ ] T015 Commit local en `feature/f14-rediseno-ui`, sin push ni PR.
