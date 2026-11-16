# Tasks: F76 · Lectura rápida de escaneos en el servidor

**Input**: `specs/057-lectura-paralela/` (spec, plan, research, data-model, contracts, quickstart)

**Formato**: `[ID] [P?] [Historia] Descripción`. `[P]` = se puede hacer en paralelo (archivos distintos, sin dependencias). Pruebas primero: cada prueba se escribe y falla antes de su implementación (principio III).

## Phase 1: Setup

- [x] T001 Añadir `openvino` a `requirements.in` con la versión fijada y regenerar `requirements.txt` con hashes (`python -m piptools compile --generate-hashes ...`), dejando `colorama` y `tzdata` al final. `python -m pip_audit --strict -r requirements.txt -r requirements-dev.txt` limpio.
- [x] T002 [P] En `tests/conftest.py`, fijar `OCR_MOTOR=onnxruntime` y `OCR_PROCESOS=1` para las pruebas que no son de F76, de modo que la suite existente no cambie de comportamiento ni de duración (SC-005).

## Phase 2: Foundational (bloquea las historias)

- [x] T003 Prueba en `tests/test_lectura_paralela.py`: `OCR_MOTOR`, `OCR_PROCESOS` y `OCR_HILOS` se leen del entorno con sus valores por defecto (`openvino`, 3, 1); un valor no válido lanza un error que nombra la variable ([contrato](contracts/configuracion.md)).
- [x] T004 Implementar en `adaptadores/extraccion.py` la lectura de esas tres variables (sin Django) y su validación.
- [x] T005 Prueba: con `OCR_MOTOR=onnxruntime`, `version_extractor()` devuelve el mismo valor que antes de F76 (valor fijado en la prueba); con `openvino`, uno distinto que cambia con la versión de `openvino`; `OCR_PROCESOS` y `OCR_HILOS` no lo alteran (FR-005, research R4).
- [x] T006 Implementar la identidad en `version_extractor()` y el motor en `_ocr()` (`Det.engine_type`, `Rec.engine_type`, hilos por motor) en `adaptadores/extraccion.py`.

**Checkpoint**: el motor es configurable y la llave de la caché lo refleja.

## Phase 3: User Story 1 · Los escaneos se leen varias veces más rápido (P1) 🎯 MVP

**Prueba independiente**: un PDF escaneado ficticio leído en serie y con 3 procesos da el mismo texto y los mismos avisos.

- [x] T007 [US1] Prueba en `tests/test_lectura_paralela.py`: un PDF ficticio de varias páginas escaneadas, leído con `OCR_PROCESOS=1` y con `OCR_PROCESOS=3` (mismo motor), da `leer_con_calidad()` idéntico: texto, orden de páginas y calidad por página (FR-001 a FR-003).
- [x] T008 [US1] Prueba: el mismo PDF con `onnxruntime` y con `openvino` da el mismo texto y los mismos `motivos`, `requiere_revision`, `intentos` y `transformacion` por página. Si una confianza difiere, la prueba informa en qué página y cuánto (FR-003).
- [x] T009 [US1] Prueba: PDF con páginas digitales y escaneadas mezcladas conserva el orden; una imagen suelta y un PDF de una página se leen sin repartir; una hoja en blanco sigue sin lectura (edge cases).
- [x] T010 [US1] Implementar el reparto en `adaptadores/extraccion.py`: grupo de procesos creado una vez (`concurrent.futures.ProcessPoolExecutor`, inicializador que carga el motor), tarea = ruta y número de página, informes recogidos por índice; `_pdf_informe` decide en el proceso principal qué páginas van al grupo y aplica después la comparación con la capa dudosa. Con 1 proceso, camino actual (research R2).
- [x] T011 [US1] Prueba y manejo de fallo: si la lectura de una página lanza una excepción en su proceso, `leer_con_calidad()` la propaga; si el proceso muere, el grupo se descarta y el siguiente documento crea uno nuevo (FR-010, research R7).
- [x] T012 [US1] Prueba en `tests/test_expedientes_worker.py`: tras un fallo de página, el documento queda en `ERROR` con el mensaje actual, sin `texto_extraido` y con el temporal borrado; `metricas` guarda `openvino`, `procesos` y `paginas` en una lectura correcta. Implementar las métricas en `expedientes/services.py`.

**Checkpoint**: la lectura rápida funciona y es idéntica a la actual.

## Phase 4: User Story 2 · La confrontación empieza antes (P2)

**Prueba independiente**: con recaudos encolados antes, el worker toma primero borrador y minuta.

- [x] T013 [P] [US2] Prueba en `tests/test_expedientes_worker.py`: `tomar_pendiente()` devuelve borradores y minutas antes que recaudos más antiguos; entre iguales, el de menor `id`; los recaudos se toman cuando no quedan borradores ni minutas (FR-008).
- [x] T014 [US2] Implementar el orden en `tomar_pendiente` de `expedientes/services.py`, conservando `select_for_update(skip_locked=True, of=("self",))`.

## Phase 5: User Story 3 · Un documento largo no se repite ni se pierde (P2)

**Prueba independiente**: la de F34 (`test_no_recupera_documento_lento_con_lock_vivo`). Al implementar se comprobó que el bloqueo existente ya impide la relectura.

- [x] T015 [US3] Retirada: el avance por página resultó redundante (research R5).
- [x] T016 [US3] Retirada: FR-009 ya lo cubre el bloqueo de F34 y su prueba existente.
- [x] T017 [US3] Retirada: sin avance que implementar.

## Phase 6: User Story 4 · El administrador controla cuánto consume (P3)

**Prueba independiente**: con `onnxruntime` y 1 proceso, el sistema se comporta como antes de F76.

- [x] T018 [P] [US4] Prueba: `procesar_documentos` con un motor no disponible (módulo ausente simulado) termina con un mensaje claro y no toma documentos.
- [x] T019 [US4] Implementar esa comprobación al arrancar en `expedientes/management/commands/procesar_documentos.py`.
- [x] T020 [P] [US4] Crear `scripts/medir_lectura_paralela.py`: genera escaneos ficticios con el generador de `scripts/medir_tiempos_ingesta.py`, recorre las configuraciones del [quickstart](quickstart.md) y escribe una línea por configuración con páginas por minuto, memoria máxima, texto idéntico y avisos idénticos; acepta una carpeta externa para la muestra privada y solo deja recuentos (FR-012).
- [x] T021 [P] [US4] Documentar las tres variables en `README.md`, `AGENTS.md` y `.env.example`, y la regla de un solo worker.

## Phase 7: Polish y validación

- [ ] T022 `python -m ruff check .`, `python -m ruff format --check .` y `python -m pytest --cov --cov-report=term --cov-report=xml:coverage.xml` en verde; cobertura del código nuevo ≥ 80 %.
- [ ] T023 Medición privada en desarrollo con `scripts/medir_lectura_paralela.py` sobre la muestra fuera del repositorio: texto y avisos idénticos en el 100 % de las páginas (SC-002). Si algún aviso cambia, detenerse y avisar antes de seguir.
- [ ] T024 **En el servidor de la notaría**: ejecutar las comprobaciones 8 a 12 del [quickstart](quickstart.md). Elegir `OCR_PROCESOS` y `OCR_HILOS` (SC-001, SC-003, SC-004).
- [ ] T025 Con el resultado de T024: actualizar los límites de recursos en `specs/046-despliegue/quickstart.md` (FR-011), la sección de F76 en `docs/mediciones-ocr.md` y la fila de F76 en `docs/roadmap.md`.
- [ ] T026 Revisar el diff: sin datos reales ni secretos; `spec.md` al día con lo implementado.

## Dependencias

- Phase 1 → Phase 2 → historias. US1 es el MVP.
- US2 (T013, T014) no depende de US1 y puede hacerse en paralelo.
- US4: T018 a T021 después de T006; T020 necesita T010.
- T024 y T025 necesitan acceso al servidor: no se pueden hacer en el equipo de desarrollo. El PR puede integrarse con la lectura rápida ya implementada y los valores por defecto, y T024 ajusta la configuración después, sin cambiar código.

## Estrategia

1. Setup y Foundational.
2. US1 completa y validada (MVP): la mejora medida.
3. US2 y US3, pequeñas e independientes entre sí.
4. US4 y la medición privada.
5. Medición en el servidor y ajuste de la configuración.
