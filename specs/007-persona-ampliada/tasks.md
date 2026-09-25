# Tasks: F12 · Persona ampliada

**Input**: `spec.md` aprobado, `research.md`, `plan.md`, `contracts/ui.md`.
**Alcance actual**: SOLO PLANIFICACIÓN. Ninguna tarea de implementación está
completada por estos documentos.

**TDD**: cada regla o corrección del núcleo empieza con un test ficticio que
falla por el motivo esperado; luego se implementa la mínima solución.

## Phase 1 — decisiones bloqueantes

- [ ] T001 Obtener del propietario la fecha de referencia para minoría de edad y documentar la respuesta en `specs/007-persona-ampliada/spec.md`; criterio: no queda `[NEEDS CLARIFICATION]` de US2 antes de implementar esa regla.
- [ ] T002 Obtener del propietario la lista cerrada de abreviaturas equivalentes y documentarla en `specs/007-persona-ampliada/spec.md`; criterio: US3 define qué normalizar y qué no.
- [ ] T003 Corregir con el propietario en `docs/catalogo-fuentes.md` las etiquetas y fronteras de domicilio/distrito RENIEC y estado civil biométrico; criterio: cada captura tiene rótulo exacto, columna y sección de página; no se infiere de números cercanos.
- [ ] T004 Resolver con el propietario en `specs/007-persona-ampliada/spec.md` la contradicción minuta/borrador y el significado por persona de «sin cónyuge»; criterio: US1, FR-005 y el flujo F5 nombran el mismo texto a comparar.
- [ ] T005 Aclarar en `docs/catalogo-datos.md` y `docs/catalogo-fuentes.md` la diferencia de muestras 28/27 frente a 30/32 y corregir la afirmación de cobertura del Input de `specs/007-persona-ampliada/spec.md`; criterio: biométrica no se atribuye fecha/domicilio sin evidencia.

**Checkpoint**: T001–T005 requieren decisiones o evidencia documental del
propietario. No inventar etiquetas, fecha ni equivalencias para avanzar.

## Phase 2 — contrato compartido y regresiones

- [ ] T006 [P] Escribir pruebas rojas en `tests/test_personas.py` de `Persona` con tres/cuatro argumentos posicionales, los ocho argumentos nuevos opcionales, valores por defecto y procedencia individual; criterio: construcciones F11 siguen válidas.
- [ ] T007 [P] Fijar en `tests/test_personas.py` la salida previa exacta de `comparar_personas()`, `revisar()` y `revisar_parrafos()` para entradas ficticias sin campos F12; criterio: FR-009/SC-005 detectan cambio de contenido u orden.
- [ ] T008 Implementar en `nucleo/verificar.py` la ampliación final de `Persona` y la procedencia por campo con tipo de página; criterio: T006 pasa y `Procedencia` F11 no cambia.
- [ ] T009 Escribir pruebas rojas en `tests/test_personas.py` para preservar los cuatro pares valor/procedencia en ambas reconstrucciones de `unificar_personas()`; criterio: ausencia no toma procedencia ajena y orden de archivos no altera ganador.

## Phase 3 — US1 estado civil (P1)

**Prueba independiente**: ficha ficticia RENIEC casada y texto aprobado que
la presenta soltera producen observación; mención válida de cónyuge no.

- [ ] T010 [US1] Escribir prueba roja en `tests/test_personas.py` para `ESTADO CIVIL` RENIEC y rótulo biométrico aprobado, por celda/columna, con género y fuente ilegible; criterio: enum SOLTERO/CASADO/VIUDO/DIVORCIADO y ninguna lectura de página no autorizada.
- [ ] T011 [US1] Escribir prueba roja en `tests/test_personas.py` para conflicto RENIEC/BIOMETRICA con orden de fuentes invertido; criterio: gana RENIEC, se conserva su procedencia y se marca revisión manual.
- [ ] T012 [US1] Implementar captura y unificación civil en `nucleo/verificar.py` reutilizando `_linea_etiquetada()`; criterio: T009–T011 pasan sin capturar operador/pie.
- [ ] T013 [US1] Escribir prueba roja en `tests/test_personas.py` para discrepancia civil, casado con cónyuge, ausencia de cónyuge según la decisión T004, fuente ilegible y persona sin documento; criterio: observación estructurada solo de la persona inequívoca.
- [ ] T014 [US1] Ampliar `comparar_personas()` en `nucleo/verificar.py` para estado civil y conflicto, preservando las observaciones previas; criterio: T007 y T013 pasan sin alterar `revisar()`.

## Phase 4 — US2 minoría de edad (P1)

**Prueba independiente**: fecha ficticia que implica 17 años en la referencia
aprobada produce edad cumplida; fecha ausente o dudosa no produce observación.

- [ ] T015 [US2] Escribir prueba roja en `tests/test_personas.py` para `FECHA DE NACIMIENTO` RENIEC con `/`, `-`, fecha imposible y carácter OCR dudoso; criterio: fecha `date`/ISO y descarte seguro.
- [ ] T016 [US2] Implementar captura de fecha en `nucleo/verificar.py` por etiqueta/columna y conservar procedencia; criterio: T009/T015 pasan.
- [ ] T017 [US2] Escribir prueba roja en `tests/test_personas.py` para cumpleaños cumplido/no cumplido, 17/18 años y fecha de referencia explícita aprobada; criterio: mismo input produce misma salida, sin reloj dentro del núcleo.
- [ ] T018 [US2] Añadir rama de edad a `comparar_personas()` en `nucleo/verificar.py` y pasar la referencia aprobada desde `expedientes/services.py`; criterio: T007/T017 pasan, sin observación si falta fecha legible.

## Phase 5 — US3 domicilio (P2)

**Prueba independiente**: domicilio ficticio ausente produce una observación;
presente con normalización aprobada no la produce.

- [ ] T019 [US3] Escribir prueba roja en `tests/test_personas.py` para rótulos RENIEC aprobados de domicilio/distrito, sección de domicilio frente a nacimiento y celda vecina; criterio: nunca se atribuye una dirección de otra sección/persona.
- [ ] T020 [US3] Implementar en `nucleo/verificar.py` la captura de domicilio literal y distrito del domicilio con procedencia propia; criterio: T009/T019 pasan, sin heurística de separación no aprobada.
- [ ] T021 [US3] Escribir prueba roja en `tests/test_personas.py` para tildes/mayúsculas, cada abreviatura aprobada, dirección ausente y falso positivo de otra persona; criterio: igualdad normalizada cerrada y observación estructurada solo para titular inequívoco.
- [ ] T022 [US3] Añadir rama de domicilio en `comparar_personas()` de `nucleo/verificar.py`; criterio: T007/T021 pasan sin búsqueda difusa.

## Phase 6 — US4 tabla y consumo F5 (P2)

**Prueba independiente**: la respuesta HTML autorizada muestra cuatro valores
y cuatro procedencias; el JSON de sondeo y logs no contienen esos datos.

- [ ] T023 [US4] Escribir prueba roja en `tests/test_expedientes_confrontacion.py` para `confrontar_borrador()` con datos ficticios, prioridad de fuente y nuevas filas `Regla` tras las históricas; criterio: no cambia `Personas`/`Ortografía` ni persiste los valores.
- [ ] T024 [US4] Implementar en `expedientes/services.py` la adaptación de observaciones estructuradas, `_personas_legibles()` y `_resumen_extraccion()` con procedencia por campo; criterio: parser de cadenas históricas no recibe dicts nuevos.
- [ ] T025 [US4] Escribir prueba roja en `tests/test_expedientes_confrontacion_ui.py` para tabla accesible, conflicto visible, autorización, escape de archivo, ausencia en endpoint de sondeo y error/logs seguros; criterio: solo HTML autorizado contiene datos personales ficticios.
- [ ] T026 [US4] Ampliar `templates/expedientes/confrontacion.html` para cuatro campos/procedencias y observaciones con persona/fuente/página; criterio: T025 pasa y conserva estado/retorno F11.

## Phase 7 — verificación final

- [ ] T027 Ejecutar `python -m pytest --cov --cov-report=term --cov-report=xml:coverage.xml`, Ruff check/format y `git diff --check`; registrar resultados en el reporte de implementación, no aquí.
- [ ] T028 Ejecutar Django `check` y `makemigrations --check`, `pip-audit --strict`, gitleaks y pre-commit aplicable; criterio: sin migración ni dependencia nueva.
- [ ] T029 Revisar diff en busca de datos reales, secretos, rutas, logs y JSON de sondeo; criterio: SC-006 y privacidad verificados con evidencia, no por inferencia.
- [ ] T030 Separar resultado local, Quality Gate remoto y medición privada `local_reference` del propietario; criterio: ninguna casilla se marca por una ejecución ajena o pendiente.
- [ ] T031 Preparar commit local en `feature/f12-persona-ampliada` solo cuando la implementación esté lista; criterio: sin push ni Pull Request salvo instrucción posterior.

## Dependencias

T001–T005 preceden a cualquier regla afectada. T006/T007 preceden a T008 y
T014/T018/T022. T009 precede a la unificación de US1–US3. US4 consume el
resultado de US1–US3; T023/T025 son rojas antes de T024/T026. T027–T031 son
gates de implementación futura. Los tests nuevos usan exclusivamente nombres,
documentos, domicilios y fechas ficticios; no se ejecuta la medición privada
en CI.
