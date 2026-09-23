# Tasks: F11 · Extracción por personas

**Input**: `specs/006-personas/plan.md`, `research.md`, `contracts/ui.md` y
`spec.md` aprobado.

**Prerequisites**: NC-001–NC-005 están resueltas en `spec.md`. No se añade
migración ni campo de páginas; las páginas nuevas se separan con `\f` y el texto
histórico sin separador se procesa como un bloque. Todos los tests usan nombres,
documentos y textos ficticios.

**Regla TDD**: cada tarea de regla empieza con una prueba roja, se comprueba
que falla por la razón correcta y solo después se implementa. En esta etapa
ninguna tarea está marcada como completada.

## Phase 1 — decisiones y evidencia

- [X] T001 [P] Incorporar `docs/catalogo-fuentes.md` al árbol desde una fuente
  autorizada o confirmar que su ausencia es intencional; criterio: la versión
  usada en esta planificación queda identificada y no contiene datos reales.
- [X] T002 Obtener decisión del propietario para NC-001 (SISGEN); criterio: la
  regla de descarte y el destino de `Documento Identificativo` quedan escritos
  sin reinterpretación del agente.
- [X] T003 Obtener decisión del propietario para NC-002 (campo de páginas,
  migración y filas F4 antiguas); criterio: no hay campo ni migración, y el
  separador vive en la cadena plana sin inventar páginas históricas.
- [X] T004 [P] Revisar que la respuesta no contradiga FR-001–FR-013 ni la
  constitución; criterio: si una respuesta cambia el contrato, se detiene la
  implementación y se solicita actualizar `spec.md`.

**Checkpoint**: T001–T004 resueltas; la implementación puede continuar.

## Phase 2 — pruebas rojas del contrato puro

- [X] T005 [P] Crear `tests/test_personas.py` con fixtures de `Pagina`, dos
  comparecientes ficticios y procedencias; criterio: el test espera `Persona`
  ligada, página y archivo, y falla antes del contrato.
- [X] T006 [P] Probar que `Catalogo` proyecta `NOMBRE`, `DNI`, `PARTIDA` y
  `MONTO`, y que `cat["DNI"]`/`cat.get("NOMBRE")` mantienen la lectura antigua;
  criterio: también se acepta un dict legado en `revisar` y `diagnostico`.
- [X] T007 [P] Probar asociación dentro de bloque: dos personas en una página
  no intercambian documentos; valores de páginas distintas nunca se juntan.
- [X] T008 [P] Probar `revisar`, `correspondencia`, `diagnostico` y
  `revisar_parrafos` contra fixtures históricos; criterio: la salida de
  partidas, montos, párrafos y diagnóstico queda idéntica antes/después.
- [ ] T009 [P] Probar documento cruzado y documento sin titular; criterio: el
  comparador nuevo devuelve estructuras de observación deterministas sin
  cambiar las cadenas de `revisar()`.

## Phase 3 — extracción por página y cache

- [X] T010 [P] Crear prueba roja de `leer_paginas()` para un PDF ficticio de dos
  páginas; criterio: cada página queda separada y `leer()` conserva la cadena
  plana compatible. Los formatos de una página mantienen la cobertura existente.
- [ ] T011 [P] Probar que PDF con texto y PDF escaneado no ejecutan OCR dos veces
  por página y que la clave de cache usa la versión de recursos existente.
- [X] T012 [P] Resolver que no habrá campo de páginas ni migración: la cadena
  plana usa `\f` como separador y conserva el texto histórico.
- [X] T013 [P] Resolver el tratamiento de texto antiguo sin separador: F5 sigue
  mostrando su extracción y F11 lo procesa como un único bloque degradado.
- [X] T014 Implementar la ruta mínima de páginas y el wrapper `leer()`; criterio:
  T010 pasa sin afectar CLI, worker, léxico ni el texto plano usado por F5.

## Phase 4 — clasificación y descarte

- [X] T015 [P] Escribir pruebas rojas de clasificación para separador, SISGEN,
  RENIEC, biométrica, declaración jurada, SUNARP, identidad, prosa y
  desconocida; criterio: la precedencia es estable y no depende del orden del
  diccionario.
- [X] T016 [P] Probar descarte completo solo de separadores y del tipo SISGEN
  resuelto por NC-001; criterio: se excluyen resultados de listas, cabeceras,
  marcas de agua y pies, y se conservan conteos sin texto.
- [X] T017 [P] Probar que una página desconocida o con OCR incompleto no se
  descarta por defecto y deja estado `revision_manual`/no clasificada.
- [X] T018 [P] Probar que partidas y montos extraídos de una página descartada
  no cambian respecto de la regla histórica; criterio: FR-013 permanece verde.
- [X] T019 Implementar clasificación y descarte conservador; criterio:
  T015–T018 pasan y ninguna cifra de ocho dígitos aislada se vuelve DNI.

## Phase 5 — etiquetas y unificación

- [ ] T020 [P] Escribir prueba roja de etiquetas `DNI`, `DNI.`, `D.N.I.`,
  `D.N.I. N°` y la errata `D.N.1,`; criterio: solo la errata acotada entra.
- [ ] T021 [P] Probar rechazo de números de operador, usuario, transacción,
  verificación, RUC, partida, teléfono, correo y resultados SISGEN; criterio:
  ningún falso positivo entra como documento.
- [ ] T022 [P] Probar `CUI` con control y el límite de DNI manuscrito partido;
  criterio: el segundo queda fuera por la decisión NC-004.
- [ ] T023 [P] Probar nombres etiquetados y `APELLIDOS, NOMBRES`; criterio:
  solo el patrón explícito se reordena, la prosa arbitraria no.
- [ ] T024 [P] Probar unificación por documento exacto y por nombre exacto sin
  documento; criterio: todas las procedencias aparecen una vez.
- [ ] T025 [P] Probar que nombres parecidos con documentos distintos y nombres
  incompatibles con un mismo documento no se unifican y quedan en revisión.
- [ ] T026 Implementar extracción localizada, tolerancia cerrada y unificación
  conservadora; criterio: T020–T025 pasan sin fuzzy matching aprobatorio.

## Phase 6 — servicio y UI

- [ ] T027 [P] Escribir pruebas rojas del servicio F5 para que las fuentes
  entreguen páginas, el borrador conserve su texto plano y el catálogo de
  personas se construya por documento/página, no por legajo concatenado.
- [ ] T028 [P] Escribir prueba roja de documento cruzado con dos personas y
  documentos intercambiados; criterio: la observación identifica esperado,
  hallado y procedencia de fuente.
- [ ] T029 [P] Escribir prueba roja de documento no titular, nombre sin DNI,
  conflicto de lecturas, páginas descartadas y página no clasificada; criterio:
  estados seguros y sin llamadas externas.
- [ ] T030 [P] Escribir pruebas rojas de UI para una persona una sola vez con
  varias procedencias, tabla accesible, recuentos y mensajes de re-subida;
  criterio: no muestra texto completo, hashes, rutas ni datos en logs.
- [ ] T031 Implementar el consumo en `expedientes/services.py`, observaciones
  nuevas y adaptación de plantilla; criterio: T027–T030 pasan, se conserva la
  autorización de F5 y el resultado no se persiste.

## Phase 7 — verificación final

- [ ] T032 Ejecutar pruebas F11 y la suite existente con cobertura; criterio:
  ningún marker privado se ejecuta por defecto y la paridad de F5 queda
  documentada con fixtures ficticios.
- [ ] T033 Ejecutar `python -m ruff check .`, `python -m ruff format --check .`
  y `git diff --check`; criterio: solo se modifican archivos previstos.
- [ ] T034 Ejecutar Django check, `makemigrations --check`, `pip-audit --strict`
  y gitleaks; F11 no crea migraciones.
- [ ] T035 Revisar diff por privacidad: ningún DNI, nombre, domicilio,
  fragmento real, secreto, ruta temporal o contenido de expediente.
- [ ] T036 Revisar `requirements.md`, `ux.md`, el contrato y la spec sin marcar
  `[X]` por inferencia; criterio: solo evidencia ejecutada queda marcada.
- [ ] T037 Preparar commit local en `feature/f11-personas`; criterio: no push,
  no Pull Request y Quality Gate/medición privada remotos se reportan aparte.

## Dependencias y estrategia

- T001–T004 están resueltas y no bloquean las tareas de código.
- T005–T009 deben estar rojas antes de implementar T014, T019 y T026.
- T010–T014 preceden al servicio de T027; T015–T019 preceden al clasificador.
- T020–T026 preceden al servicio y UI de T027–T031.
- T032–T037 solo se ejecutan cuando la implementación esté verde.

La entrega incremental es contrato puro + adaptador de páginas, luego
clasificación y finalmente documento cruzado/unificación y UI. Las filas F4
antiguas sin separador se procesan como un único bloque; no se simula una
compatibilidad de página inventada.
