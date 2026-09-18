# Tasks: F1 · Base DevSecOps

**Input**: `specs/001-base-devsecops/`: spec.md, plan.md, research.md, data-model.md, contracts/ci.md y quickstart.md.
**Prerequisites**: Constitución 1.2.0 y roadmap F1; ejecutar `$speckit-analyze` antes de implementar.
**Organization**: Las seis etapas y sus commits siguen la instrucción expresa del usuario; dentro de cada etapa las etiquetas US1/US2/US3 conservan trazabilidad con las historias. Setup y fundamentos se incluyen en etapas 1–2; cierre transversal en etapa 6.
**Tests**: Requeridos por la spec. Toda corrección de comportamiento comienza con una prueba ficticia que falla. No crear script ni suite del agregado CI.
**Format**: `- [ ] Tnnn [P?] [USn] acción y ruta`. `[P]` solo permite trabajo independiente dentro de su etapa tras satisfacer los prerrequisitos indicados.

Los commits indicados son tareas de implementación, no commits realizados por generar este documento. Cada checkpoint registra evidencia saneada en `specs/001-base-devsecops/quickstart.md`: comandos, estado y enlaces/identificadores de ejecución, nunca datos de clientes. Commit local al final de cada etapa, solo con sus archivos revisados; no publicar historia ni usar bypass. Los checkpoints de etapas 1–4 no autorizan merge. La cláusula de arranque de la constitución v1.3.0 permite PR 1 al cerrar etapa 5 con cuatro checks; PR 2 completa F1 con cinco controles y agregado, sin enmienda pendiente. Ante bloqueo externo, registrar el estado y no marcar la tarea como terminada.

## Etapa 1 · Saneamiento — US1 (P1)

**Objetivo**: contenido y nombres actuales ficticios antes de cualquier análisis remoto.
**Prueba independiente**: revisión local del árbol y diff sin datos reales ni secretos; repositorio privado e historia intacta.

- [X] T001 [US1] Registrar en `specs/001-base-devsecops/quickstart.md` el inventario de alcance a sanear en código, tests, documentación y rutas, sin transcribir valores reales; comprobar localmente estado Git y privacidad del remoto sin activar SonarQube.
- [X] T002 [US1] Sustituir datos reales en `test_extraer.py`, `test_verificar.py`, `test_lexico.py`, `test_ortografia.py` y `test_revisor_llm.py` por datos ficticios coherentes, preservando casos y expectativas sin copiar documentos reales.
- [X] T003 [US1] Sanear cualquier dato real encontrado en el resto del código/documentación versionados del alcance de T001 y renombrar referencias de fixtures a nombres neutros en `test_*.py` y `tests/fixtures/`; no incluir nombres antiguos en mensajes de commit ni informes.
- [X] T004 [US1] Revisar `.gitignore` para conservar exclusión de expedientes y secretos y añadir artefactos locales de calidad; mantener el historial sin reescribir y documentar en `specs/001-base-devsecops/quickstart.md` que publicar exige limpieza histórica en otra fase.
- [X] T005 [US1] Ejecutar checkpoint de saneamiento de contenido, nombres, referencias y diff; registrar solo alcance/resultado en `specs/001-base-devsecops/quickstart.md`, sin enviar contenido ni historia a Cloud y sin confundir detección de secretos con revisión de datos personales.
- [X] T006 [US1] Crear commit local `chore: sanitize repository data` con los cambios revisados de `test_*.py`, `.gitignore` y las rutas saneadas en T003–T005; comprobar que no incluye archivos privados ni valores originales.

**Checkpoint**: T005 aprobado y T006 creado. Los fallos existentes por ausencia de fixtures o compatibilidad aún se registran como pendientes de etapas 2–3; no iniciar análisis Cloud.

## Etapa 2 · Fixtures sintéticos y pytest — US1 (P1)

**Objetivo**: conservar los casos sin expedientes privados; disponer de ejecución local explícita para la medición real.
**Prueba independiente**: regenerar expediente desde clon limpio, recolectar los casos y verificar que no se leen archivos reales por defecto ni en CI.

- [X] T007 [US1] Crear `requirements-dev.txt` con versiones compatibles fijadas de pytest y pytest-cov para Python 3.13, y configurar en `pyproject.toml` descubrimiento de `test_*.py` de raíz y `tests/`, marker estricto `local_reference` y exclusión predeterminada del marker.
- [X] T008 [US1] Convertir `test_extraer.py`, `test_verificar.py`, `test_lexico.py`, `test_ortografia.py` y `test_revisor_llm.py` en funciones recolectables por pytest, conservando cada caso; hacer fallar primero los casos contra los fixtures sintéticos aún ausentes y mantener el filtrado determinista sin llamadas a modelos.
- [X] T009 [US1] Implementar `scripts/generar_fixtures.py` para crear en `tests/fixtures/` textos, imagen OCR, PDF con/sin texto, documentos con notas, tablas y borradores correctos/incorrectos enteramente ficticios usando stdlib y bibliotecas existentes; nombres/metadatos estables y sin documentos reales como plantilla.
- [X] T010 [P] [US1] Implementar `tests/conftest.py` y `tests/test_referencia_local.py` con selección explícita local, ruta externa `EXPEDIENTES_REFERENCIA_DIR` y rechazo de ejecución real bajo CI; lectura solo durante el test, nunca al importar; fallos saneados por archivos ausentes y resumen agregado sin datos personales.
- [X] T011 [P] [US1] Configurar cobertura en `pyproject.toml` para módulos productivos incluidos los no importados, XML con rutas relativas y exclusión de tests/generador del denominador; exigir informe parseable con al menos una línea productiva, sin imponer un 80 % global que sustituya el umbral de código nuevo.
- [X] T012 [US1] Documentar en `specs/001-base-devsecops/quickstart.md` aprovisionamiento reproducible de OCR y diccionario es_PE con versiones/orígenes y ejecución del generador; adaptar los tests de T008 al expediente generado y no descargar expedientes en ninguna prueba.
- [X] T013 [US1] Ejecutar checkpoint de recolección, repetición de generación y selección local/CI de `test_*.py` y `tests/`; registrar en `specs/001-base-devsecops/quickstart.md` todos los casos conservados, resultados y únicamente el fallo conocido de textutil en Linux como pendiente de etapa 3, sin skips permanentes ni xfail que lo oculten.
- [X] T014 [US1] Crear commit local `test: add synthetic fixtures and pytest` con `scripts/generar_fixtures.py`, `test_*.py`, `tests/`, `pyproject.toml`, `requirements-dev.txt` y guía revisados; no añadir salidas privadas o documentos ignorados a la fuerza.

**Checkpoint**: todos los casos recolectados y no legacy en verde, sin acceso real predeterminado; fallo Linux identificado para etapa 3. T014 creado. US1 completa su ejecución Linux al terminar etapa 3.

## Etapa 3 · LibreOffice en Linux — US1 (P1)

**Objetivo**: conservar formatos antiguos en Linux con la adaptación mínima del lector compartido.
**Prueba independiente**: tests de conversión real con documentos sintéticos, éxito, errores y limpieza temporal.

- [X] T015 [US1] Añadir primero en `test_extraer.py` casos ficticios fallidos de lectura/conversión legacy en Linux, ausencia o fallo del ejecutable y limpieza temporal; identificar todos los callers de `_legacy` en `extraer.py` antes de cambiarlo.
- [X] T016 [US1] Adaptar `_legacy` en `extraer.py` a LibreOffice headless en Linux con argumentos sin shell, timeout, directorio temporal y perfil aislado; preservar comportamiento macOS cuando corresponda, validar resultados y no emitir contenido sensible en errores.
- [X] T017 [US1] Ajustar generación/conversión legacy en `scripts/generar_fixtures.py` y `test_extraer.py` para que deje de requerir textutil en Linux; documentar el ejecutable y aprovisionamiento en `specs/001-base-devsecops/quickstart.md` sin introducir nuevas abstracciones.
- [ ] T018 [US1] Ejecutar checkpoint de toda la suite sintética en Linux y repetibilidad con `test_extraer.py` y `test_*.py`; comprobar errores/limpieza y medir no regresión local si se alteró el núcleo, registrando únicamente resultados saneados en `specs/001-base-devsecops/quickstart.md`. **Pendiente: medición local_reference con EXPEDIENTES_REFERENCIA_DIR, la ejecuta el usuario en su máquina antes del merge de PR 1 (extraer.py cambió)**.
- [X] T019 [US1] Commit local creado: `2be5a48` — `Finalizar etapa 3` (mensaje distinto al previsto `fix: support legacy documents on Linux`); T018 permanece pendiente de medición local.

**Checkpoint**: suite sintética completa en verde en Linux y T019 creado; T018 pendiente de medición local antes del merge de PR 1. MVP US1: etapas 1–3, sin activar Cloud aún.

## Etapa 4 · Ruff y pip-audit en verde — US2 (P1)

**Objetivo**: llevar código existente a verde con reglas de seguridad activas.
**Prueba independiente**: ruff check/format y pip-audit estricto pasan en entorno limpio; tests conservan resultados.

- [X] T020 [US2] Añadir ruff, pip-audit y pre-commit con versiones fijadas en `requirements-dev.txt`; configurar en `pyproject.toml` E4/E7/E9/F y S más formato, con `[tool.ruff.lint.per-file-ignores]` exactamente `"test_*.py" = ["S101"]` y `"tests/**" = ["S101"]`; S101 permitido en tests por per-file-ignores; cualquier otra excepción S solo como noqa individual con código y motivo, listada en el PR.
- [X] T021 [US2] Aplicar formato y corregir hallazgos Ruff del código Python existente, incluidos `extraer.py`, `verificar.py`, `lexico.py`, `ortografia.py`, scripts, interfaces y pruebas; crear primero test fallido ficticio ante cualquier corrección de comportamiento, sin excluir archivos para obtener verde.
- [X] T022 [US2] Ejecutar pip-audit estricto sobre `requirements.txt` y `requirements-dev.txt` con transitivas y corregir versiones vulnerables preservando compatibilidad; documentar en el PR cualquier ID exceptuado y razón individual, sin ignorar errores de resolución/red ni categorías completas.
- [X] T023 [US2] Actualizar `AGENTS.md` y `specs/001-base-devsecops/quickstart.md` con comandos reales F1 de tests, lint y auditoría, política S101 documentada una sola vez y evidencia de versiones resueltas; mantener fuera del ERP las dependencias IA.
- [X] T024 [US2] Ejecutar checkpoint en entorno limpio: ruff check, format --check, pytest con cobertura y pip-audit --strict; comprobar S101 fuera de tests y otra regla S dentro de tests con muestras ficticias temporales, y registrar resultados en `specs/001-base-devsecops/quickstart.md` sin añadir una suite para configuración trivial.
- [X] T025 [US2] Crear commit local `chore: pass lint and dependency audit` con `pyproject.toml`, requisitos, código corregido y documentación tras T024 aprobado; justificar solo hallazgos admitidos por la política, no cada assert.

**Checkpoint**: estilo, seguridad Ruff, pruebas y dependencias en verde; cobertura válida; T025 creado. Sonar aún no activado.

## Etapa 5 · CI, pre-commit y Dependabot — US2 (P1) / US3 (P2)

**Objetivo**: configuración completa de controles automáticos y prevención local; activación Cloud queda en etapa 6.
**Prueba independiente**: PR 1 con cuatro controles en verde, sin sonar ni agregado; tras merge, main ejecuta esos cuatro controles.

- [ ] T026 [US2] Crear `.github/workflows/ci.yml` para cada PR sin filtros por rutas/destino y push a main con jobs `lint`, `tests`, `dependencies`, `secrets`; runner efímero Ubuntu 24.04, Python 3.13, permisos lectura, acciones fijadas a SHA verificado, checkout sin credenciales persistentes y timeout de 30 minutos.
- [ ] T027 [US2] Completar en `.github/workflows/ci.yml` generación de fixtures, LibreOffice/recursos OCR y diccionario, pytest excluyendo local_reference, validación XML y transferencia privada de coverage.xml por revisión/intento durante 7 días; pip-audit estricto y gitleaks fijado/redactado sobre árbol y commits introducidos, sin enviar expedientes ni publicar workspace o historia.
- [ ] T028 [US2] Preparar `sonar-project.properties` para fuentes/tests/cobertura antes de futura conexión Cloud, sin token ni activar análisis; en `.github/workflows/ci.yml` mantener únicamente los cuatro jobs de PR 1, sin sonar ni ci-required ni pull_request_target.
- [ ] T029 [P] [US3] Crear `.pre-commit-config.yaml` con revisiones fijadas para ruff check, format --check y gitleaks redactado; documentar instalación y ejecución manual en `specs/001-base-devsecops/quickstart.md`.
- [ ] T030 [P] [US3] Crear `.github/dependabot.yml` para pip y github-actions semanalmente, sin auto-merge y sujeto a los checks vigentes; incluir requisitos productivos y de desarrollo.
- [ ] T031 [US3] Probar `.pre-commit-config.yaml` con fallos exclusivamente ficticios y corrección exitosa; revisar programación de `.github/dependabot.yml`; registrar evidencia saneada en `specs/001-base-devsecops/quickstart.md`.
- [ ] T032 [US2] Realizar validación previa local de `.github/workflows/ci.yml`, tests, lint, auditoría y secretos; revisar diff saneado y configuración de los cuatro checks sin sonar/ci-required; registrar checkpoint previo en `specs/001-base-devsecops/quickstart.md`.
- [ ] T033 [US2] Crear commit de cierre `ci: add initial quality checks` con `.github/workflows/ci.yml`, `.github/dependabot.yml`, `.pre-commit-config.yaml`, `sonar-project.properties` y guía; hacer push de la rama privada, sin reescribir historia.
- [ ] T034 [US2] Abrir PR 1 en borrador con etapas 1–5; verificar lint, tests, dependencies y secrets de `.github/workflows/ci.yml` en verde para el SHA final; registrar enlaces en `specs/001-base-devsecops/quickstart.md`. Corregir mediante commits/push adicionales si hace falta, nunca falsear checks.
- [ ] T035 [US2] Pasar PR 1 a listo y mergearlo solo con los cuatro checks en verde, sin bypass ni force push; documentar en la descripción del PR la excepción única de arranque y el alcance de `.github/workflows/ci.yml`. Si las reglas actuales impiden merge, detenerse sin modificarlas para eludirlas.
- [ ] T036 [US2] Verificar tras el merge la ejecución de los cuatro checks en main y registrar SHA/ejecución en `specs/001-base-devsecops/quickstart.md`; no conectar Cloud si la main integrada no está saneada y validada.

**Checkpoint**: PR 1 integrado, cuatro checks de main aprobados y commit de etapa conservado. No afirmar F1 completa.

## Etapa 6 · PR 2: SonarQube y protección — US2 (P1) / cierre US3

**Objetivo**: completar la puerta de calidad y protección permanente sin ciclos de integración.
**Prueba independiente**: PR 2 solo se integra con cinco controles y agregado en verde; comprobación final de main después del merge.

- [ ] T037 [US2] Tras T036, verificar capacidades/privacidad y alcance saneado de `sonar-project.properties`, cobertura y metadatos SCM; el usuario conecta SonarQube Cloud privado y realiza el primer análisis de main saneada, con cobertura del mismo SHA. Registrar enlace/estado en `specs/001-base-devsecops/quickstart.md`; esperar al usuario si aún no lo ha conectado, sin comprar servicios ni pedir tokens en chat.
- [ ] T038 [US2] Crear rama de PR 2 desde main; a partir del primer análisis, inventariar y corregir o justificar por escrito todas las vulnerabilidades, bugs y Security Hotspots existentes, con pruebas ficticias fallidas antes de correcciones de comportamiento en los módulos afectados; documentar resoluciones en PR 2 y evidencia en `specs/001-base-devsecops/quickstart.md`. Registrar code smells existentes como deuda no bloqueante con ID/enlace en `docs/deuda-f3.md`; no desactivar reglas ni excluir archivos.
- [ ] T039 [US2] Comprobar que `.specify/memory/constitution.md` v1.3.0 (TODO(SONAR) resuelto y cláusula de arranque) cubre lo implementado, sin nueva enmienda salvo discrepancia real; sincronizar referencias en `docs/roadmap.md` sin declarar F1 terminada.
- [ ] T040 [US2] Añadir `sonar` a `.github/workflows/ci.yml`, aislado y dependiente de tests, con cobertura del mismo SHA/intento, token solo en el escáner y espera del gate de 300 s; preparar secretos por el responsable en Actions/Dependabot, nunca valores en archivos. No ejecutar código/dependencias del PR en el job de análisis ni usar pull_request_target; fallar sin credenciales o gate calculado.
- [ ] T041 [US2] Añadir `ci-required` a `.github/workflows/ci.yml` con exactamente `needs: [lint, tests, sonar, dependencies, secrets]`, `if: always()` y un único paso `test "${{ join(needs.*.result, ',') }}" = "success,success,success,success,success"`, sin helper, checkout, suite propia o continue-on-error.
- [ ] T042 [US2] Configurar gate Cloud con nuevas vulnerabilidades=0, bugs=0, hotspots revisados=100 %, cobertura nueva>=80 % y tolerancia de cambios pequeños desactivada; verificar que code smells antiguos no bloquean y no se han reducido mínimos de código nuevo. Registrar ajustes en `specs/001-base-devsecops/quickstart.md`.
- [ ] T043 [US2] Realizar validación previa de PR 2: tests/lint/auditoría/secretos locales, evidencia de hallazgos existentes atendidos, deuda F3, medición local sin regresión si cambió núcleo y diff saneado; actualizar `AGENTS.md` y `specs/001-base-devsecops/quickstart.md` sin exigir todavía comprobación posterior al merge.
- [ ] T044 [US2] Crear commit de etapa `ci: complete SonarQube quality gate` con `.github/workflows/ci.yml`, `sonar-project.properties`, `docs/deuda-f3.md` y documentación; hacer push de la rama PR 2 sin reescribir historia.
- [ ] T045 [US2] Abrir PR 2 y verificar cinco controles y ci-required de `.github/workflows/ci.yml` en verde para el SHA actual; probar fallos de controles, cancelación/omisión, cobertura/credenciales ausentes, umbrales de gate, cambios pequeños y sin código productivo nuevo según `specs/001-base-devsecops/contracts/ci.md`. Usar solo ejemplos ficticios, retirar los cambios de prueba y verificar el SHA final.
- [ ] T046 [US3] Verificar PR de Dependabot y PR documental con `.github/dependabot.yml` y `.github/workflows/ci.yml`: mismos controles, bloqueo y sin auto-merge; registrar enlaces en `specs/001-base-devsecops/quickstart.md`, sin ensayo de forks ni SHA obsoleto separado.
- [ ] T047 [US2] Configurar y verificar protección final de main con los seis checks publicados, rama actualizada, PR obligatorio, cero reviews requeridas, sin bypass/force push; registrar reglas y verificación en `specs/001-base-devsecops/quickstart.md`, mediante commit/push adicional si corresponde y revalidar SHA final.
- [ ] T048 [US2] Mergear PR 2 únicamente tras cinco controles y agregado en verde y protección verificada conforme a `specs/001-base-devsecops/contracts/ci.md`; no usar bypass para cerrar F1.
- [ ] T049 [US2] Verificar ejecución de cinco controles y agregado en main después de T048 y completar matriz FR/SC de `specs/001-base-devsecops/spec.md`; registrar resultado saneado en la evidencia del PR y actualizar `docs/roadmap.md` solo por el flujo de PR protegido. Declarar F1 terminada únicamente con esta verificación.

**Checkpoint**: commit de etapa y PR 2 integrados; ejecución final en main verificada. Evidencia posterior al merge en el PR, sin escribir directamente en main.

## Dependencies & Execution Order

```text
Etapas 1–4 → etapa 5: validar → commit/push → PR 1 → merge → verificar main
→ usuario conecta Cloud y analiza main → etapa 6: preparar PR 2
→ validar → commit/push → PR 2 → checks/protección → merge → verificar main
```

US1 se completa en etapas 1–3; US2 entrega cuatro controles en PR 1 y puerta completa en PR 2; US3 se valida localmente en etapa 5 y remotamente en T046. Solo el arranque PR 1 tiene excepción de cuatro checks, formalizada en la enmienda de PR 2 según la decisión expresa del usuario.

## Parallel Examples por historia

- US1: T010 y T011, después de T009, trabajan en archivos distintos.
- US2: secuencial por configuración compartida, operaciones remotas y dependencias de resultados.
- US3: T029 y T030 trabajan en archivos distintos; integrar antes de T031.

## Implementation Strategy

MVP técnico: etapas 1–3. Primera integración: PR 1 con etapas 1–5 y cuatro checks reales en verde. Segunda integración: PR 2 con etapa 6 y puerta completa. No sustituir validaciones remotas por presencia de archivos. Las tareas pendientes de conexión Cloud por el usuario no se marcan completas. No avanzar a F2/F3: únicamente registrar deuda de code smells existentes para F3.
