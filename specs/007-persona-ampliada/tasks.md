# Tasks: F12 · Persona ampliada

**Fuentes**: `spec.md`, `research.md`, `plan.md`, `contracts/ui.md`.
**Ronda actual**: contrato de persona, cuatro capturas RENIEC y tabla de
extracción. Las reglas US1–US3 se ejecutan en la siguiente ronda por instrucción
del propietario. `[X]` indica evidencia ya producida; gates pendientes no se
marcan por anticipado.

## Phase 1 — decisiones documentales

- [X] T001 Fijar edad a la fecha de hoy y exigir que la observación muestre esa fecha (`spec.md` US2).
- [X] T002 Fijar la lista cerrada de equivalencias de domicilio (`spec.md` US3).
- [X] T003 Corregir fuente y rótulos: solo RENIEC; distinguir distrito de domicilio del de nacimiento y excluir el pie (`spec.md` FR-002; catálogos).
- [X] T004 Fijar el borrador y la cláusula de la persona como alcance de US1 (`spec.md` Clarifications).
- [X] T005 Corregir la medición estricta de campos RENIEC y la atribución falsa a biométrica (`docs/catalogo-datos.md`, `docs/catalogo-fuentes.md`).

## Phase 2 — contrato y regresiones, ronda actual

- [X] T006 Escribir prueba roja para constructor posicional de tres/cuatro argumentos, ocho opciones nuevas y procedencia por campo (`tests/test_personas.py`).
- [X] T007 Fijar la salida literal y orden de `comparar_personas()`, `revisar()` y `revisar_parrafos()` con la misma entrada ficticia (`tests/test_personas.py`).
- [X] T008 Ampliar `Persona` al final sin cambiar las cuatro posiciones existentes (`nucleo/verificar.py`).
- [X] T009 Probar y conservar pares valor/procedencia en ambas reconstrucciones de `unificar_personas()`, con fuente sin campos antes y después (`tests/test_personas.py`, `nucleo/verificar.py`).

## Phase 3 — captura RENIEC, ronda actual

- [X] T010 Probar página RENIEC ficticia a dos columnas con los cuatro valores y procedencias, y pie biométrico que no produce estado civil (`tests/test_personas.py`).
- [X] T011 Probar `CASADA`, `casado`, `CASADO.`, fecha válida con `/` o `-`, fecha imposible y OCR dudoso (`tests/test_personas.py`).
- [X] T012 Leer solo rótulos al inicio de línea y su columna en RENIEC; nunca `DISTRITO DE NACIMIENTO`, biométrica ni pie (`nucleo/verificar.py`).
- [X] T013 Normalizar enum civil y fecha, conservar dirección y distrito legibles, descartar valores dudosos sin procedencia (`nucleo/verificar.py`).

## Phase 4 — tabla y privacidad, ronda actual

- [X] T014 Probar proyección de cuatro valores y procedencias con nombre de archivo sin ruta (`tests/test_expedientes_confrontacion.py`).
- [X] T015 Probar HTML autorizado con cuatro campos y cuatro procedencias (`tests/test_expedientes_confrontacion_ui.py`).
- [X] T016 Ampliar `_personas_legibles()` y tabla de extracción; conservar `expediente_estado()` y logs sin datos F12 (`expedientes/services.py`, `templates/expedientes/confrontacion.html`).
- [X] T017 Verificar ausencia de campos F12 en sondeo, errores y logs mediante pruebas focalizadas; revisar escape y autorización de HTML.

## Phase 5 — verificaciones y entrega, ronda actual

- [X] T018 Ejecutar `python scripts/generar_fixtures.py` y suite completa con cobertura.
- [X] T019 Ejecutar Ruff check/format, Django `check` y `makemigrations --check`.
- [X] T020 Ejecutar `git diff --check`, revisar diff por privacidad y confirmar ausencia de migraciones/dependencias.
- [X] T021 Commit local en `feature/f12-persona-ampliada`, sin push ni PR; separar evidencia local, Quality Gate remoto y medición privada pendiente.

## Phase 6 — siguiente ronda: reglas de confrontación

- [ ] T022 TDD de estado civil frente a la cláusula de la persona en el borrador; incluir soltero/casado, cónyuge en otra cláusula, dato ausente y persona sin documento.
- [ ] T023 TDD de minoría de edad con cumpleaños cumplido/no cumplido y fecha de hoy pasada por el servicio al núcleo.
- [ ] T024 TDD de domicilio con toda la lista cerrada de equivalencias, orden del número y atribución segura por persona.
- [ ] T025 Capturar fecha de emisión de dos consultas RENIEC antes de elegir el estado civil más reciente; marcar conflicto para revisión manual.
- [ ] T026 Adaptar las nuevas observaciones estructuradas a la sección Regla y completar UI, privacidad y paridad F5.
- [ ] T027 Ejecutar medición privada `local_reference` fuera de CI antes de integrar; gate del propietario.

No se usan datos reales en pruebas, fixtures, código ni commit. La fase 6 no
forma parte del commit de esta ronda.
