# Feature Specification: F1 · Base DevSecOps

**Feature Branch**: `feature/f1_devsecops`

**Created**: 2026-09-17

**Status**: Especificación validada

**Input**: User description: "Cada Pull Request y cada push a main ejecutan automáticamente: lint con ruff (incluidas reglas de seguridad), tests con cobertura, análisis de SonarQube con Quality Gate, auditoría de dependencias (pip-audit) y búsqueda de secretos (gitleaks). Un PR no se puede mergear si algo falla. Antes del primer análisis se eliminan de los tests los DNI y apellidos reales, reemplazándolos por datos ficticios. También se configura pre-commit y Dependabot."

**Decisión del usuario**: SonarQube Cloud, con el código saneado antes del primer análisis. Arranque en dos PRs, amparado por la cláusula de arranque de la constitución v1.3.0: PR 1 integra etapas 1–5 con cuatro checks en verde; tras su merge el usuario conecta Cloud y analiza main saneada; PR 2 completa etapa 6, enmienda y protección. La excepción se formaliza en la constitución en PR 2; no se usa bypass.

## Clarifications

### Session 2026-09-17
- Q: ¿Cómo se conservan en CI los casos que dependen de expedientes? → A: Crear un expediente sintético en tests/fixtures/, generado por script sin datos reales. La medición completa con expedientes reales queda en tests marcados de ejecución exclusivamente local.
- Q: ¿Qué se hace con el historial y los nombres de archivos de fixtures? → A: F1 no reescribe el historial; el repositorio permanece privado. Publicarlo exige limpiar el historial en otra fase. Se renombran los archivos de fixtures para eliminar nombres reales.
- Q: ¿Qué alcance tiene F1 sobre los hallazgos del código existente? → A: Dejar el código existente en verde: formato corregido y hallazgos corregidos o justificados por escrito, sin exclusiones globales de reglas.
- Q: ¿Se requieren aprobaciones de revisores para integrar en main? → A: Mientras haya un único mantenedor, solo se exigen los checks obligatorios, sin aprobaciones requeridas; se conserva la integración por PR.

Las reglas de cinco controles y gate siguientes describen el estado final de F1. FR-013 delimita exclusivamente el PR 1 de arranque; no se extiende a PR posteriores.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Analizar sin exponer datos personales (Priority: P1)

Como responsable del repositorio, quiero que los tests y el material enviado a análisis contengan únicamente datos ficticios para evitar exponer información de clientes.

**Why this priority**: El saneamiento es requisito previo al primer análisis.

**Independent Test**: Revisar localmente el contenido que se analizará y ejecutar las pruebas con sustitutos ficticios, sin publicar valores originales en los resultados de la revisión.

**Acceptance Scenarios**:

1. **Given** tests con datos reales, **When** se prepara el primer análisis, **Then** se sustituyen DNI, nombres, apellidos, domicilios y fragmentos reales por ejemplos ficticios coherentes, conservando los casos y sus resultados esperados; también se renombran los archivos de fixtures y sus referencias para eliminar nombres reales.
2. **Given** contenido pendiente de revisar o datos reales detectados, **When** se intenta iniciar el análisis, **Then** no se envía ese contenido hasta completar el saneamiento y su revisión.
3. **Given** una copia limpia del repositorio saneado, **When** se genera el expediente sintético mediante el script y se ejecutan las pruebas obligatorias, **Then** se conservan los casos unitarios en CI sin expedientes privados ni datos reales en logs o informes.
4. **Given** las pruebas marcadas de medición completa, **When** se ejecuta CI o la suite predeterminada, **Then** no se ejecutan; solo una selección explícita local permite medir contra expedientes reales externos al repositorio, sin emitir sus datos.

---

### User Story 2 - Integrar solo cambios verificados (Priority: P1)

Como mantenedor, quiero ver los controles de cada cambio y que una comprobación fallida impida integrarlo en `main`.

**Why this priority**: Evita que defectos y problemas de seguridad entren en la rama compartida.

**Independent Test**: Usar cambios de prueba ficticios que provoquen por separado cada fallo obligatorio y comprobar el bloqueo; después corregirlos y comprobar que la última revisión queda habilitada para merge.

**Acceptance Scenarios**:

1. **Given** un PR abierto o actualizado, **When** se recibe una nueva revisión, **Then** se ejecutan automáticamente lint y formato, tests con cobertura, análisis estático y de seguridad con puerta de calidad, auditoría de dependencias y búsqueda de secretos.
2. **Given** un push a `main`, **When** se recibe el cambio, **Then** se ejecuta el mismo conjunto de controles y se muestran sus resultados para esa revisión.
3. **Given** cualquier control fallido, ausente, pendiente, omitido o cancelado, **When** se intenta mergear el PR, **Then** la integración permanece bloqueada.
4. **Given** todos los controles aprobados para la última revisión y un único mantenedor, **When** se intenta mergear el PR, **Then** se permite la integración sin requerir aprobaciones de revisores; un resultado verde de una revisión anterior no basta.
5. **Given** un intento de escritura directa en `main`, **When** se intenta evitar el PR, **Then** la protección lo rechaza, también para administradores dentro de las reglas configuradas.
6. **Given** un incumplimiento de cualquiera de los umbrales de FR-005, **When** se evalúa la puerta de calidad, **Then** falla y bloquea el merge.
7. **Given** el código existente, **When** se completa F1, **Then** cumple el formato y los controles quedan en verde, con vulnerabilidades, bugs y Security Hotspots existentes corregidos o justificados por escrito; los code smells existentes quedan registrados como deuda F3 sin bloquear. No se permiten exclusiones globales de reglas.

---

### User Story 3 - Detectar problemas antes del commit y mantener dependencias (Priority: P2)

Como colaborador, quiero comprobar mis cambios localmente y recibir propuestas de actualización para corregir dependencias sin omitir la revisión habitual.

**Why this priority**: Reduce correcciones tardías y mantiene visibles las actualizaciones necesarias.

**Independent Test**: Activar los controles locales siguiendo la documentación, intentar un commit con un fallo ficticio y verificar que una propuesta automática de actualización pasa por los controles del PR.

**Acceptance Scenarios**:

1. **Given** pre-commit instalado y activado, **When** se intenta un commit con un fallo de lint, formato o un secreto de prueba detectable, **Then** el commit se detiene e identifica el control que requiere corrección sin revelar el secreto.
2. **Given** controles locales omitidos, **When** se abre el PR, **Then** los controles remotos siguen siendo obligatorios.
3. **Given** una actualización disponible en las dependencias supervisadas, **When** se ejecuta la revisión periódica, **Then** Dependabot puede crear un PR sujeto a los mismos controles, sin merge automático.

### Edge Cases

- Una caída del servicio de análisis o la ausencia de credenciales deja el PR bloqueado; nunca se interpreta como aprobación.
- Un PR sin acceso a secretos, incluido uno de un fork, no recibe credenciales ni una aprobación ficticia para suplir controles que no pudieron ejecutarse.
- Los cambios solo de documentación y los PR de Dependabot también requieren los controles obligatorios.
- Una ejecución sin pruebas recolectadas o sin informe de cobertura válido no cuenta como satisfactoria.
- Los expedientes de referencia privados permanecen fuera del repositorio y del CI; no se suben para resolver fallos por archivos ausentes. Si se selecciona explícitamente la medición local y faltan esos archivos, se informa la ausencia sin datos personales y no se presenta la medición como aprobada.
- F1 no reescribe el historial y el repositorio permanece privado. Hacerlo público exige una fase aparte de limpieza del historial. Si una herramienta requiere recibir historial con datos reales, el análisis queda bloqueado hasta poder cumplir el requisito de no enviarlos; la privacidad del repositorio no sustituye al saneamiento del contenido enviado.
- Un hallazgo sin corrección disponible sigue bloqueando mientras no exista una excepción documentada admisible según la constitución; no se permite omitir controles completos.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Antes del primer análisis se DEBEN sanear los tests, renombrar archivos de fixtures y actualizar sus referencias para eliminar nombres reales, y revisar todo el contenido que se enviará, incluido historial si forma parte de la entrada. No se envía contenido histórico con datos reales. F1 NO reescribe el historial: el repositorio DEBE permanecer privado y su publicación requiere limpiar el historial en una fase aparte. La evidencia de revisión identifica alcance y resultado sin copiar datos originales. Cubre US1 y el caso de historial privado.
- **FR-002**: Un script DEBE generar de forma reproducible un expediente totalmente sintético en `tests/fixtures/`, conservando los casos unitarios y resultados esperados en CI desde un clon limpio. Las pruebas de medición completa contra expedientes reales DEBEN estar marcadas, excluidas de CI y de la ejecución predeterminada, y ejecutarse solo mediante selección explícita local con expedientes externos al repositorio. Los tests versionados no incluyen datos reales ni los imprimen. La migración completa del núcleo sigue en F3. Cubre US1.3–4.
- **FR-003**: Cada PR y cada push a `main` DEBEN ejecutar automáticamente los controles exigidos por el usuario y la constitución: GitHub Actions, ruff con formato y reglas de seguridad S, pytest con cobertura, SonarQube Cloud con Quality Gate, pip-audit y gitleaks. Son restricciones explícitas, no decisiones de implementación nuevas. Única salvedad: el PR de arranque definido en FR-013 se integra con los cuatro controles disponibles, conforme a la cláusula de arranque de la constitución v1.3.0; la regla de los cinco controles rige desde el PR que activa SonarQube. Cubre US2.1–2.
- **FR-004**: Los resultados DEBEN identificar revisión, control y estado, y ofrecer información suficiente para corregir el fallo sin exponer datos personales ni secretos. Cubre US2.1–4 y US3.1.
- **FR-005**: El Quality Gate DEBE exigir como mínimo, sobre código nuevo, cero vulnerabilidades, cero bugs nuevos críticos o bloqueantes, 100 % de Security Hotspots revisados y cobertura de al menos 80 %. Debe existir medición de cobertura válida; la ausencia de datos no constituye aprobación. Cubre US2.6.
- **FR-006**: `main` DEBE aceptar integraciones solo mediante PR con todos los controles obligatorios aprobados para la última revisión. Ningún fallo, estado pendiente, cancelación, omisión ni resultado ausente permite merge; la protección no admite bypass configurado para administradores o automatizaciones. Mientras haya un único mantenedor, solo se exigen los checks obligatorios para aprobar el PR, con cero aprobaciones de revisores requeridas. Cubre US2.3–5.
- **FR-007**: La auditoría DEBE bloquear ante dependencias vulnerables detectadas por defecto. Cualquier excepción DEBE quedar documentada con alcance y justificación en el PR, conforme a la constitución; no convierte una ejecución fallida en verde ni permite desactivar la auditoría. Un falso positivo o hallazgo aceptado requiere justificación escrita. Cubre US2.3 y el caso de hallazgo sin corrección.
- **FR-008**: pre-commit DEBE ofrecer comprobaciones locales de lint, formato y secretos; su instalación, activación y ejecución manual DEBEN estar documentadas. Omitirlo no altera los requisitos remotos. Cubre US3.1–2.
- **FR-009**: Dependabot DEBE revisar semanalmente las dependencias Python y las acciones de CI, y proponer actualizaciones mediante PR sin integración automática. Cubre US3.3.
- **FR-010**: La documentación DEBE indicar cómo ejecutar tests y lint desde F1, interpretar los controles, configurar la protección y aprovisionar credenciales sin incluir sus valores. Las instrucciones de agentes DEBEN reflejar los comandos de F1. Cubre US2 y US3.
- **FR-011**: El análisis DEBE ejecutarse en SonarQube Cloud, según la elección del usuario, únicamente con contenido saneado. La constitución v1.3.0 ya resolvió TODO(SONAR) y autorizó la cláusula de arranque, por lo que el primer análisis de main saneada ocurre entre PRs sin necesidad de una enmienda posterior. Se verifica por la modalidad configurada.

- **FR-012**: F1 DEBE dejar el código existente en verde: formato aplicado y vulnerabilidades, bugs y Security Hotspots existentes corregidos o justificados individualmente por escrito en el PR según la constitución. Los code smells existentes no bloquean y se registran como deuda para F3; esta excepción no reduce el gate de código nuevo ni las reglas Ruff. No se permiten exclusiones globales de reglas para lograrlo. Se permite S101 únicamente en archivos de pruebas mediante per-file-ignores para `test_*.py` y `tests/**`, sin justificar cada assert. S101 permitido en tests por per-file-ignores; cualquier otra excepción S solo como noqa individual con código y motivo, listada en el PR. Esta política se documenta una vez en el PR. Una justificación no elimina los umbrales de FR-005 ni permite mergear controles fallidos. Cubre US2.7.

- **FR-013**: El arranque DEBE dividirse en dos PRs: PR 1 (etapas 1–5) con lint, tests, dependencies y secrets en verde, sin jobs sonar ni ci-required; tras su merge, el usuario conecta Cloud y analiza main saneada. PR 2 (etapa 6) incorpora sonar, ci-required de cinco dependencias y protección final de main, al amparo de la constitución v1.3.0 ya vigente. No se usa bypass. Validación previa, commit/push, PR, merge y verificación de main son pasos separados.

### Requisitos de seguridad

- Los colaboradores pueden ejecutar controles locales y consultar resultados según los permisos del repositorio; solo responsables autorizados administran secretos y protecciones. El CI accede únicamente a los recursos necesarios para sus controles.
- El repositorio permanece privado durante F1; se verifica esta condición antes del primer análisis. Los nombres de fixtures y sus referencias tampoco contienen nombres reales.
- Los datos tratados por los controles remotos son código saneado, metadatos de revisiones, resultados de pruebas, cobertura y hallazgos. Nunca expedientes privados ni contenido personal real, tampoco en informes o mensajes.
- Las credenciales se aprovisionan mediante los almacenes autorizados por la constitución; nunca en código, documentación, chat o logs. Código de PR no confiable no puede obtenerlas.
- Se valida la procedencia de los resultados y su correspondencia con la última revisión; un control local no sustituye al obligatorio remoto.
- Los controles de CI no añaden servicios de IA ni dependencias de internet al ERP en ejecución.

### Key Entities *(include if feature involves data)*

- **Revisión de cambio**: versión concreta del código asociada a un PR o a `main`.
- **Resultado de control**: control, revisión evaluada, estado y evidencia saneada; determina si la integración es admisible.
- **Hallazgo y excepción**: problema detectado, gravedad y, cuando corresponda, justificación escrita y alcance de la excepción revisable en el PR.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % del contenido incluido en el primer análisis ha sido revisado y contiene cero datos personales reales, incluidos nombres de archivos de fixtures y referencias. Todos los casos de prueba obligatorios usan sustitutos ficticios sin perder sus resultados esperados. Se verifica que el repositorio permanece privado y que F1 no reescribe el historial.
- **SC-002**: Desde el PR que activa SonarQube, el 100 % de los PR y cambios recibidos en la rama principal obtiene resultados de los cinco grupos de controles: estilo, pruebas, calidad y seguridad del código, dependencias y secretos. El PR de arranque de FR-013 obtiene los cuatro grupos disponibles (estilo, pruebas, dependencias y secretos).
- **SC-003**: El 100 % de los intentos de integración con un control fallido, ausente, pendiente, omitido, cancelado o perteneciente a una revisión anterior queda bloqueado. Con un único mantenedor, un PR de la última revisión con todos los controles aprobados puede integrarse sin aprobaciones de revisores.
- **SC-004**: Cada cambio aceptado cumple los mínimos de código nuevo: cero vulnerabilidades, cero defectos críticos o bloqueantes, revisión del 100 % de puntos sensibles de seguridad y cobertura mínima del 80 %.
- **SC-005**: En un clon limpio, el expediente ficticio se puede regenerar con los mismos resultados y el 100 % de los casos unitarios conservados se ejecuta sin expedientes privados. Ninguna prueba de medición real corre en CI ni en la selección predeterminada; la medición completa puede ejecutarse explícitamente en local. Una persona colaboradora puede identificar el control y la revisión responsables de cada fallo de prueba.
- **SC-006**: Los controles locales impiden los commits de prueba defectuosos y la revisión semanal de dependencias queda activada; las propuestas automáticas pasan por las mismas barreras que las humanas.

- **SC-007**: Al cerrar F1, todos los controles del código existente están en verde, el 100 % de sus vulnerabilidades, bugs y Security Hotspots tiene corrección o justificación individual escrita; sus code smells existentes están registrados como deuda F3 y no bloquean y no se han introducido exclusiones globales de reglas.

- **SC-008**: PR 1 se integra con los cuatro controles aprobados y su ejecución en main verificada; el primer análisis usa esa main saneada. PR 2 se integra con los cinco controles y agregado aprobados, sin bypass; su ejecución final en main queda verificada.

## Assumptions

- Alcance exclusivo: F1 del roadmap. No incluye pantallas, roles de notaría, migración completa del núcleo, OCR, almacenamiento de expedientes ni despliegue del ERP.
- Las herramientas nombradas por el usuario y la constitución son requisitos impuestos. Versiones, configuración concreta y distribución de trabajos pertenecen al plan.
- Se adopta revisión semanal de dependencias y ausencia de merge automático como valores iniciales. La auditoría bloquea por defecto todos sus hallazgos, salvo excepciones documentadas admisibles.
- Hay un único mantenedor; la política de aprobaciones se revisará cuando cambie esta condición.
- Se dispone de un repositorio privado con soporte para controles obligatorios y protección de `main`, y de acceso administrativo para configurarlos; si falta, F1 no puede declararse implantada solo por añadir archivos.
- El acceso a SonarQube Cloud debe permitir análisis de PR y exigir su puerta de calidad. Su disponibilidad y las credenciales son dependencias de implantación; no se solicitan valores secretos ni se presupone un plan comercial concreto.
- El saneamiento conserva relaciones entre valores y resultados esperados. La medición con expedientes privados se mantiene separada; si durante F1 se cambia el núcleo, aplica la exigencia constitucional de no regresión.
