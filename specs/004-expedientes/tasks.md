# Tasks: F4 · Expedientes

**Input**: `spec.md`, `data-model.md`, `research.md`, `contracts/ui.md` y
`plan.md` de `specs/004-expedientes/`.

**Regla de esta etapa**: este archivo solo planifica. No se crea código de
aplicación ni migraciones hasta una etapa posterior.

**TDD**: cada prueba marcada como roja debe ejecutarse y comprobarse fallida
antes de implementar su comportamiento. Todos los datos de pruebas son
ficticios y no se incluyen expedientes, textos ni archivos reales.

## Etapa 1: pruebas de contrato y modelo (tests primero)

- [ ] T001 [P] Añadir pruebas rojas de `Expediente`, estados iniciales,
  normalización de `codigo`, unicidad y relaciones protegidas en
  `tests/test_expedientes_models.py`; criterio: la suite falla porque la app y
  los modelos aún no existen, y no contiene datos personales.
- [ ] T002 [P] Añadir pruebas rojas de `Documento` y `TextoExtraido` para roles,
  estados, tamaños positivos, unicidades `(expediente, rol, hash_archivo)` y
  `(hash_archivo, version_extractor)` en `tests/test_expedientes_models.py`;
  criterio: cada regla del `data-model.md` tiene una aserción distinguible.
- [ ] T003 [P] Añadir pruebas rojas de visibilidad por creador y Administrador,
  incluyendo denegación de expediente ajeno en HTML, JSON, reintento y
  eliminación de documento (FR-013), en
  `tests/test_expedientes_permissions.py`; criterio: las rutas inexistentes o
  sin autorización fallan antes de cualquier implementación.
- [ ] T004 [P] Añadir pruebas rojas de creación y subida en una sola pantalla,
  validación de código/rol/extensión/tamaño/contenido y rechazo de duplicados
  en `tests/test_expedientes_upload.py`; criterio: se verifican mensajes sin
  datos personales y no se escribe temporal cuando la validación previa falla.
- [ ] T005 [P] Añadir pruebas rojas del servicio de hash, nombres temporales
  controlados, transición y bloque `finally` en éxito/error en
  `tests/test_expedientes_services.py`; criterio: un archivo ficticio nunca
  permanece tras ambas rutas y el hash SHA-256 coincide con la entrada.
- [ ] T006 [P] Añadir pruebas rojas de caché por `(hash, version_extractor)`,
  reutilización y actualización de `ultimo_uso_el`, incluida la concurrencia
  de dos altas, en `tests/test_expedientes_services.py`; criterio: el segundo
  uso no llama al extractor y una versión distinta sí crea una entrada nueva.
- [ ] T007 [P] Añadir pruebas rojas del consumidor: `PENDIENTE` a
  `PROCESANDO` a `LISTO`/`ERROR`, limpieza en `finally`, no doble toma y
  recuperación de `PROCESANDO` con más de 15 minutos (FR-014) en
  `tests/test_expedientes_worker.py`; criterio: el umbral se lee de settings y
  una fila vencida vuelve a `PENDIENTE`.
- [ ] T008 [P] Añadir pruebas rojas de reintento, estado JSON/polling, estado
  vacío, todos listos, error recuperable y accesibilidad textual en
  `tests/test_expedientes_ui.py`; criterio: se cubren los estados y mensajes
  de `contracts/ui.md` sin afirmar contenido documental.
- [ ] T009 [P] Añadir pruebas rojas de los comandos de huérfanos y supresión en
  `tests/test_expedientes_commands.py`; criterio: se conserva hash/metadatos,
  se eliminan solo temporales con más de 24 h y una supresión vacía las
  entradas compartidas e informa el conteo afectado (FR-015).
- [ ] T010 [P] Añadir prueba roja de identidad del extractor en
  `tests/test_extractor_identity.py`; criterio: cambiar un hash de
  `_OCR_FILES` o `_OCR_USE_CLS` cambia la identidad y no se ejecuta OCR real.

**Checkpoint**: comprobar el rojo de T001–T010, revisar que no haya datos
reales/secretos y crear el commit local de tests rojos antes de implementar.

## Etapa 2: base de la aplicación y persistencia

- [ ] T011 Crear `expedientes/apps.py`, registrar la app en
  `config/settings.py` y añadir las rutas base en `config/urls.py`;
  criterio: `manage.py check` reconoce la app sin modificar `accounts/` ni
  `core/`.
- [ ] T012 Implementar las entidades y restricciones de
  `expedientes/models.py` según `data-model.md`, sin inventar campos ni reglas;
  criterio: T001–T002 pasan en PostgreSQL y el estado inicial es determinista.
- [ ] T013 Crear la migración inicial en
  `expedientes/migrations/0001_initial.py`; criterio: migraciones aplican y
  revierten en una base ficticia, y `makemigrations --check` queda limpio.
- [ ] T014 Añadir la configuración del directorio temporal, el máximo por
  defecto de 25 MB y el umbral de recuperación por defecto de 15 minutos en
  `config/settings.py`; criterio: ambos límites son configurables, el
  directorio no está bajo rutas estáticas/servidas y una configuración
  inválida falla de forma segura.
- [ ] T015 Ampliar `tests/conftest.py` y la configuración de cobertura para
  incluir `expedientes/`, usando fixtures ficticios reutilizables; criterio: la
  cobertura XML sigue teniendo rutas relativas y no incorpora `tests/` como
  código productivo.

**Checkpoint**: `manage.py check`, migraciones, T001–T003 y tests de fixtures
verdes; revisar solo la app nueva y los cambios mínimos de configuración.

## Etapa 3: servicios, identidad y extracción

- [ ] T016 Implementar la función pública mínima de identidad en
  `adaptadores/extraccion.py`, reutilizando `_OCR_FILES` y `_OCR_USE_CLS` sin
  cambiar `leer`, `_ocr` ni `_cacheado`; criterio: T010 pasa y las pruebas
  existentes de extracción permanecen verdes.
- [ ] T017 Implementar validación de extensión, tamaño, firma/contenido, hash y
  nombre temporal controlado en `expedientes/services.py` y, solo si hace
  falta, `expedientes/forms.py`; criterio: T004 rechaza entradas inválidas
  antes de persistir y nunca usa el nombre original como ruta.
- [ ] T018 Implementar en `expedientes/services.py` la creación de
  `TextoExtraido`, reutilización atómica, `ultimo_uso_el` y enlace a
  `Documento`; criterio: T005–T006 pasan ante uso secuencial y concurrente.
- [ ] T019 Implementar la orquestación de extracción en `services.py`, con
  estados, errores seguros, procesamiento de formatos mediante el adaptador y
  borrado en `finally`; criterio: T005 y los casos vacío/corrupto de T007 pasan
  sin texto, rutas ni trazas en la respuesta.
- [ ] T020 Implementar la toma transaccional de documentos en
  `expedientes/management/commands/procesar_documentos.py`; criterio: T007
  evita doble consumidor, recupera estados tras 15 minutos según settings
  (FR-014) y no ejecuta lógica de negocio en la vista.

**Checkpoint**: pruebas de servicios/worker y extracción sintética verdes,
Ruff sobre los archivos afectados y revisión de que el núcleo no cambió.

## Etapa 4: vistas, rutas y UI

- [ ] T021 Implementar formularios de código y subida en
  `expedientes/forms.py`; criterio: T004 pasa con validación server-side,
  errores españoles y sin duplicar reglas en plantillas.
- [ ] T022 Implementar vistas delgadas en `expedientes/views.py` y URLs en
  `expedientes/urls.py` para listado, alta, detalle, subida, estado JSON,
  reintento y eliminación confirmada del documento (FR-013); criterio:
  T003/T004/T008 pasan y cada vista solo autoriza, valida, llama servicios y
  renderiza/responde.
- [ ] T023 Crear las plantillas en `templates/expedientes/` usando el layout
  AdminLTE 4 de F2 y Alpine.js local; criterio: T008 encuentra estados,
  mensajes, etiquetas, foco, navegación y polling sin CDN, React ni HTMX.
- [ ] T024 Revisar respuestas JSON y mensajes para excluir texto, nombres,
  hashes, rutas y trazas; criterio: T003/T008 y una búsqueda de secretos/datos
  personales pasan en el diff de F4.

**Checkpoint**: pruebas de UI y permisos verdes, revisión manual del contrato
de interfaz y de las 10 heurísticas mediante `checklists/ux.md` sin marcar
ítems automáticamente.

## Etapa 5: comandos de limpieza y supresión

- [ ] T025 Implementar `limpiar_temporales` en
  `expedientes/management/commands/limpiar_temporales.py`; criterio: T009
  elimina únicamente huérfanos mayores de 24 horas, vacía `ruta_temporal` y
  no toca filas recientes ni datos extraídos.
- [ ] T026 Implementar `suprimir_texto_expediente` en
  `expedientes/management/commands/suprimir_texto_expediente.py`; criterio:
  T009 vacía la entrada `TextoExtraido` compartida para todos sus expedientes,
  informa el conteo afectado (FR-015), conserva metadatos exigidos y no borra
  filas.
- [ ] T027 Añadir `expedientes/admin.py` solo para consultas operativas mínimas
  permitidas por la decisión de seguridad; criterio: no crea una pantalla de
  gestión de cuentas ni bypass de permisos y no expone texto por defecto.

**Checkpoint**: ambos comandos se prueban con datos ficticios, y queda
documentada la evidencia agregada sin rutas/contenido.

## Etapa 6: gates y cierre de implementación

- [ ] T028 Verificar antes del cierre que tamaño máximo, recuperación,
  eliminación de documentos y supresión compartida respetan las decisiones
  aprobadas; el expediente no almacena estado ni tiene cierre.
- [ ] T029 Ejecutar `python manage.py check`, `makemigrations --check`,
  migraciones PostgreSQL, `pytest --cov --cov-report=xml:coverage.xml`, Ruff,
  `pip-audit --strict` y la suite existente; criterio: todos los gates locales
  en verde y sin medición privada en CI.
- [ ] T030 Revisar diff y árbol completo por datos reales, secretos, imports de
  `experimental/`, dependencias nuevas, llamadas IA, rutas servidas para
  temporales y cambios accidentales en `accounts/`, `core/` o `nucleo/`;
  criterio: auditoría limpia y `git diff --check` verde.
- [ ] T031 Registrar en `specs/004-expedientes/` únicamente resultados
  agregados y pendientes, sin reescribir `spec.md`/`data-model.md` por cuenta
  propia; criterio: la revisión independiente puede trazar FR/SC a pruebas y
  no se declara Quality Gate remoto desde la evidencia local.

**Checkpoint final**: revisión del agente no implementador, commit local de la
implementación posterior y PR separado; esta etapa de planificación termina
antes de T011 y no crea código.

## Dependencias y orden

- T001–T010 preceden T011–T015; no se implementa antes de comprobar el rojo.
- T011–T015 preceden servicios y vistas.
- T016 debe preceder T018–T020 porque forma parte de la llave de caché.
- T017–T020 preceden T021–T024.
- T025–T027 cubren limpieza, supresión compartida y consultas operativas ya
  decididas.
- T028–T031 son gates finales; no sustituyen pruebas ni evidencia remota.

## Oportunidades paralelas

- T001–T010 pueden redactarse en paralelo porque tienen archivos de prueba
  separados, pero el checkpoint rojo es común.
- T011 y T016 son independientes; T017–T019 deben permanecer ordenadas por la
  ruta de limpieza/caché.
- T023 y la preparación de T025 pueden avanzar en archivos separados tras
  estabilizar el contrato, sin marcar el checklist automáticamente.

## MVP técnico

T001–T024 cubren crear/subir/ver estados y procesar documentos. La
reutilización y la limpieza de temporales son obligatorias dentro de ese MVP;
la supresión compartida y los huérfanos se cierran en T025–T027. No se
implementa F5.
