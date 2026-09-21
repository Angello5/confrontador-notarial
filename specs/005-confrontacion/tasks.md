# Tasks: F5 · Confrontación

**Input**: `specs/005-confrontacion/plan.md`, `spec.md`, `research.md` y
`contracts/ui.md`.

**Prerequisites**: F4 ya integrado en `origin/main`; PostgreSQL y las
dependencias fijadas ya están disponibles. F5 no añade entidades ni
dependencias, pero incluye la migración reversible de roles de `Documento`.

**Tests**: obligatorios por la especificación y por el principio III. Cada
prueba nueva se escribe y se comprueba en rojo antes de implementar el código
que la satisface. Solo se usan textos, nombres y números ficticios.

**Organization**: historias en prioridad aprobada; US1 y US2 son P1, US3 es
P2 y US4 es P3. US1 entrega el MVP del cálculo y la acción; las demás historias
completan la lectura, advertencia y recuperación.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: dejar explícita la superficie de archivos que se puede tocar y
conservar los límites de F4/F5.

- [X] T001 Revisar `specs/005-confrontacion/research.md`, `plan.md` y `contracts/ui.md` contra `nucleo/verificar.py`, `nucleo/ortografia.py` y `expedientes/services.py`; criterio: el núcleo permanece sin cambios, los tres roles y la migración reversible quedan documentados y no se añaden dependencias ni locks.
- [X] T002 [P] Preparar los módulos de pruebas ficticias `tests/test_expedientes_confrontacion.py` y `tests/test_expedientes_confrontacion_ui.py`; criterio: pytest los descubre con los marcadores existentes, no contienen datos personales reales y fallan de forma controlada cuando referencian el servicio/ruta aún inexistente.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: reutilizar modelos, autorización y recursos locales de F4 sin
crear una entidad o infraestructura nueva.

- [X] T003 [P] Añadir en `tests/test_expedientes_confrontacion.py` fixtures/helpers sintéticos para `Expediente`, fuentes, borradores y `TextoExtraido`; criterio: permiten construir documentos `LISTO` con texto y estados bloqueantes sin escribir archivos reales ni alterar migraciones.
- [X] T004 Verificar en `tests/test_expedientes_confrontacion_ui.py` el contrato de autorización existente con un caso rojo de usuario sin rol, creador, Administrador y expediente ajeno; criterio: la acción futura exige la misma regla `usuario_puede_ver_expediente` y nunca revela la existencia de un expediente ajeno.

**Checkpoint**: fixtures y límites listos; no se implementa una capa nueva de
persistencia, cola, API o autenticación.

## Phase 3: User Story 1 - Confrontar el borrador contra las fuentes (Priority: P1) 🎯 MVP

**Goal**: pedir la confrontación de un borrador listo, ejecutar regla y
ortografía sobre textos F4 y recibir un resultado en memoria sin guardar filas.

**Independent Test**: con una fuente y un borrador ficticios `LISTO`, la acción
devuelve las observaciones sembradas; repetirla devuelve la misma estructura y
no crea ni modifica entidades de resultado.

### Tests for User Story 1 (write first)

- [X] T005 [P] [US1] Escribir en `tests/test_expedientes_confrontacion.py` pruebas rojas de precondición y orquestación: `CLIENTE`, `MINUTA` y `BORRADOR` disponibles, fuentes pasadas a `catalogo` y `diagnostico` con `nombre_original` como clave, párrafos solo para `MINUTA` y umbral fijo 88; criterio: fallan antes de implementar y detectan un rol faltante, una clave temporal, una clasificación por extensión o umbral expuesto.
- [X] T006 [P] [US1] Escribir en `tests/test_expedientes_confrontacion.py` una prueba roja de ejecución de regla + ortografía, sin léxico ni `experimental/`, usando mocks/recursos de diccionario ficticios; criterio: comprueba que los nombres del catálogo se pasan como `propios` y que ambos grupos llegan al resultado.
- [X] T007 [P] [US1] Escribir en `tests/test_expedientes_confrontacion_ui.py` pruebas rojas del POST de confrontación para creador y Administrador, método inválido/CSRF y documento que no es borrador; criterio: solo el acceso autorizado llega al servicio y las denegaciones no revelan datos.

### Implementation for User Story 1

- [X] T008 [US1] Implementar en `expedientes/services.py` la selección validada del borrador y sus fuentes `CLIENTE`/`MINUTA`, la comprobación de los tres roles, texto no vacío/estado `LISTO` y la construcción del `dict[str, str]` con claves `Documento.nombre_original`; criterio: T005 pasa, no se confrontan cadenas vacías, no se toca el núcleo y cada borrador se mantiene separado.
- [X] T009 [US1] Implementar en `expedientes/services.py` la orquestación determinista `diagnostico` → `revisar`/`revisar_parrafos` con umbral interno 88 → `nucleo.ortografia.revisar`, cargando recursos desde `adaptadores.diccionario` y pasando palabras propias del catálogo; criterio: T006 pasa, no se llama léxico/IA, el resultado es en memoria y dos ejecuciones iguales son idénticas.
- [X] T010 [US1] Añadir en `expedientes/urls.py` y `expedientes/views.py` la acción POST por documento borrador, reutilizando `_expediente_visible`, `usuario_puede_ver_expediente` y servicios existentes; criterio: T007 pasa, requiere login/rol/CSRF, valida pertenencia y rol `BORRADOR`, y renderiza sin persistir el resultado.
- [X] T011 [US1] Crear la base de `templates/expedientes/confrontacion.html` y añadir en `templates/expedientes/detalle.html` la acción/estado por borrador, con breadcrumbs, estado `TRABAJANDO`, estado sin observaciones y mensaje seguro; criterio: la acción solo se habilita con precondiciones válidas y ninguna plantilla muestra texto completo, hashes, rutas ni términos técnicos.

**Checkpoint MVP**: T005–T011 verdes; un expediente ficticio listo se puede
confrontar desde la pantalla y el núcleo permanece sin diff.

## Phase 4: User Story 2 - Entender cada observación (Priority: P1)

**Goal**: presentar campo, hallado, esperado, ubicación y motivo de cada fila,
agrupado por regla u ortografía.

**Independent Test**: un borrador ficticio con un valor alterado y una palabra
incorrecta muestra sus líneas, fragmentos cortos, valor esperado/motivo y
sugerencia, sin cambiar la salida del núcleo.

### Tests for User Story 2 (write first)

- [X] T012 [P] [US2] Escribir en `tests/test_expedientes_confrontacion.py` pruebas rojas del parser de strings de regla `[CAMPO] «valor» debe decir «X»`, `no coincide`, `FALTA` y `[PARRAFO]` con porcentaje; criterio: cada forma produce campo, hallado, esperado y ubicación esperados sin depender del orden de la lista.
- [X] T013 [P] [US2] Escribir en `tests/test_expedientes_confrontacion.py` pruebas rojas de ubicación sobre texto ficticio: línea 1/múltiples líneas, mayúsculas o tildes normalizadas, valor repetido una sola vez y valor ausente como `No ubicada`; criterio: la búsqueda vive en aplicación y conserva el fragmento original acotado.
- [X] T014 [P] [US2] Escribir en `tests/test_expedientes_confrontacion.py` prueba roja del mapeo de tuplas de ortografía `(palabra, motivo, sugerencia)` incluyendo `?`; criterio: devuelve palabra, motivo, sugerencia o `Sin sugerencia` y ubicación, sin parsear una string inventada.
- [X] T015 [P] [US2] Escribir en `tests/test_expedientes_confrontacion_ui.py` pruebas rojas de agrupación, recuentos, columnas accesibles y estado vacío; criterio: Regla y Ortografía se distinguen, los grupos muestran recuento y una confrontación limpia no se pinta como error.
- [X] T015a [P] [US2] Escribir pruebas de contrato con salida real de `nucleo.verificar.revisar()` y `revisar_parrafos()` sobre catálogo, minuta y borrador ficticios sembrados; criterio: el parser reconoce todas las observaciones producidas (DNI, nombre, monto, faltante y párrafo alterado) y ninguna cae en formato desconocido.

### Implementation for User Story 2

- [X] T016 [US2] Implementar en `expedientes/services.py` el parser de observaciones de regla y la búsqueda de línea/fragmento en el texto original del borrador; criterio: T012 y T013 pasan, los formatos desconocidos se manejan de forma segura y el núcleo no cambia.
- [X] T017 [US2] Implementar en `expedientes/services.py` el adaptador de las tuplas de ortografía y la forma común de observación; criterio: T014 pasa y los nombres propios validados no generan falsos avisos de ortografía.
- [X] T018 [US2] Completar `templates/expedientes/confrontacion.html` con tablas agrupadas por capa, recuentos, campo/palabra, hallado, esperado, motivo, porcentaje y ubicación; criterio: T015 pasa, la pantalla no expone la lista cruda del núcleo ni texto completo.
- [X] T019 [US2] Completar `tests/test_expedientes_confrontacion_ui.py` y `expedientes/views.py` para mensajes de espera, falta de datos, resultado sin hallazgos y errores seguros; criterio: los mensajes indican la acción siguiente, usan `role`/`aria-live`, foco/teclado y no incluyen trazas, rutas o datos personales.

**Checkpoint**: T012–T019 verdes; una persona autorizada puede corregir cada
hallazgo sin buscar a ciegas y la salida sigue siendo determinista.

## Phase 5: User Story 3 - Detectar un borrador que no es de este expediente (Priority: P2)

**Goal**: bloquear la lista campo por campo cuando el diagnóstico indica que el
borrador no comparte las identidades esperadas con las fuentes.

**Independent Test**: un borrador ficticio sin coincidencias y con identidades
ficticias propias muestra solo una advertencia y cero filas de comparación.

### Tests for User Story 3 (write first)

- [X] T020 [P] [US3] Añadir en `tests/test_expedientes_confrontacion.py` prueba roja de diagnóstico bloqueante y no bloqueante; criterio: el caso ajeno devuelve advertencia sin ejecutar `revisar`, párrafos ni ortografía, y un anexo sin identidades no se bloquea por error.
- [X] T021 [P] [US3] Añadir en `tests/test_expedientes_confrontacion_ui.py` prueba roja del panel de advertencia separado, con mensaje para revisar que archivos pertenezcan al mismo expediente; criterio: no aparece tabla campo por campo ni se filtra el contenido del núcleo.

### Implementation for User Story 3

- [X] T022 [US3] Ajustar `expedientes/services.py` para devolver el estado `ADVERTENCIA_CORRESPONDENCIA` y el texto seguro de `diagnostico` antes de construir observaciones; criterio: T020 pasa y no se calcula ortografía cuando el diagnóstico bloquea.
- [X] T023 [US3] Ajustar `templates/expedientes/confrontacion.html` y `expedientes/views.py` para renderizar el panel de advertencia como alerta distinta de una observación; criterio: T021 pasa y el usuario entiende que debe revisar las fuentes y el borrador.

**Checkpoint**: el borrador ajeno se detiene antes del listado y los casos sin
identidad siguen la decisión de `diagnostico()` del núcleo.

## Phase 6: User Story 4 - Texto suprimido (Priority: P3)

**Goal**: explicar que un texto eliminado por F4 no puede confrontarse y pedir
que el archivo se vuelva a subir.

**Independent Test**: un documento `LISTO` con `TextoExtraido.texto == ""` no
entra al núcleo, muestra estado no disponible y mantiene intacto el registro.

### Tests for User Story 4 (write first)

- [X] T024 [P] [US4] Añadir en `tests/test_expedientes_confrontacion.py` prueba roja para texto suprimido en fuente y borrador, y para estado nulo/pendiente; criterio: el servicio devuelve `NO_DISPONIBLE` sin llamar al núcleo y sin modificar `TextoExtraido`.
- [X] T025 [P] [US4] Añadir en `tests/test_expedientes_confrontacion_ui.py` prueba roja del botón deshabilitado/mensaje de volver a subir; criterio: la pantalla no presenta «faltan todos los campos» ni parece un fallo de servidor.

### Implementation for User Story 4

- [X] T026 [US4] Integrar en `expedientes/services.py`, `expedientes/views.py` y el detalle existente la respuesta `NO_DISPONIBLE` para texto nulo/vacío y estados no listos; criterio: T024 y T025 pasan, no se crean filas ni archivos de resultado.

**Checkpoint**: supresión y procesamiento incompleto se distinguen de un
resultado con diferencias.

## Phase 7: Polish & Cross-Cutting Validation

**Purpose**: comprobar trazabilidad, calidad local y límites de privacidad antes
de entregar la implementación a revisión.

- [X] T027 [P] Ejecutar y revisar `python -m pytest tests/test_expedientes_confrontacion.py tests/test_expedientes_confrontacion_ui.py --cov --cov-report=term --cov-report=xml:coverage.xml`; criterio: pruebas nuevas verdes, cobertura XML válida y ningún marker privado ejecutado.
- [X] T028 [P] Ejecutar `python -m ruff check .`, `python -m ruff format --check .` y `git diff --check`; criterio: gates locales verdes y solo archivos previstos modificados.
- [X] T029 [P] Revisar `tests/conftest.py`, `.github/workflows/ci.yml`, locks y diff completo; criterio: no hay dependencia nueva, secreto, dato personal, import `experimental/`, llamada IA, ruta temporal o entidad accidental; la migración de roles esperada está incluida.
- [X] T030 Verificar contra `specs/005-confrontacion/contracts/ui.md`, `checklists/requirements.md` y `checklists/ux.md`; criterio: cada FR/SC y cada estado tiene prueba o evidencia local, los ítems pendientes siguen claramente pendientes y no se afirma Quality Gate remoto.
- [X] T031 Ejecutar el checkpoint completo de `AGENTS.md` (Django check, `makemigrations --check`, migración nueva aplicada/revertida, pytest con cobertura, Ruff, `pip-audit --strict` y pre-commit si ya está habilitado); criterio: gates locales en verde, sin medición `local_reference` en CI y commit local preparado sin push.

**Evidencia T027**: las pruebas F5 actualizadas pasan de forma aislada; el hook de
cobertura exige el inventario productivo completo del repositorio, por lo que
la validez de `coverage.xml` se comprobó con la suite completa (196 pasadas,
4 privadas omitidas, 88% total).

## Dependencias y orden

### Dependencias por fase

- Setup T001–T002 → Foundation T003–T004 → US1 T005–T011 → US2 T012–T019 → US3 T020–T023 → US4 T024–T026 → Polish T027–T031.
- No se escriben entidades nuevas; la migración reversible de roles se ejecuta antes del resto de F5 y F4 conserva sus estados.
- US2 depende de la forma de resultado de US1; US3 depende de la ruta y del estado de resultado; US4 puede validarse sobre la precondición compartida, pero se cierra después para mantener la prioridad documental aprobada.

### Oportunidades paralelas

- T003 y T004 pueden prepararse en paralelo después de T002, porque usan archivos distintos.
- T005–T007 son pruebas independientes; deben quedar rojas antes de T008–T011.
- T012–T015 son pruebas independientes; deben quedar rojas antes de T016–T019.
- T020–T021 y T024–T025 son pruebas independientes dentro de sus fases.
- T027–T029 son gates independientes después de la implementación; T030–T031 dependen de sus resultados.

## Parallel Example: User Story 1

```text
T005: prueba de precondiciones, fuentes/minutas y umbral en tests/test_expedientes_confrontacion.py
T006: prueba de regla + ortografía sin léxico en tests/test_expedientes_confrontacion.py
T007: prueba de POST/autorización en tests/test_expedientes_confrontacion_ui.py
```

## Implementation Strategy

### MVP first

1. Completar Setup y Foundation sin tocar el núcleo.
2. Ejecutar T005–T007 en rojo.
3. Completar US1 (T008–T011) y validar una confrontación ficticia autorizada.
4. Detenerse para revisión: US1 es el MVP; US2–US4 completan la experiencia y los límites de seguridad.

### Incremental delivery

1. US1 entrega el cálculo y la acción.
2. US2 transforma las salidas en observaciones corregibles y accesibles.
3. US3 evita resultados inútiles para borradores ajenos.
4. US4 evita tratar una supresión como una cadena vacía.
5. Polish ejecuta solo gates locales; PR, Sonar Quality Gate y mediciones privadas quedan fuera de este commit.

## Notes

- Todas las tareas mantienen checkbox, ID secuencial, marcador `[P]` solo
  cuando corresponde, etiqueta `[USn]` en historias y ruta exacta.
- No se marca ninguna tarea como completada durante la planificación.
- Un cambio de comportamiento del núcleo requeriría detenerse, justificarlo en
  `research.md` y medirlo contra el expediente de referencia; por defecto está
  prohibido.
