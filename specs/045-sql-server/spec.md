# Feature Specification: F63 · Base de datos en SQL Server

**Feature Branch**: `feat/f63-sql-server`

**Created**: 2026-10-24

**Status**: Draft

**Input**: User description: "La notaría exige que la base del ERP esté en SQL Server, el motor que ya opera en su servidor SQLSERVER (Windows Server 2019), en lugar de PostgreSQL. El ERP debe funcionar exactamente igual que hoy (mismas pantallas, mismas reglas, mismos resultados de confrontación) con su propia base y su propio usuario en ese SQL Server, separados de los otros sistemas de la notaría. Aún no hay datos de producción (el despliegue es F8): cambia el motor, no se migran datos."

## Origen

El 2026-10-24 el usuario informó que la notaría exige que los datos del ERP vivan en SQL Server, el motor que su servidor SQLSERVER ya ejecuta para sus otros sistemas. La constitución 2.1.0 (enmendada en esta misma rama) fija SQL Server como base del ERP.

Hoy el ERP solo funciona sobre PostgreSQL. La revisión del código encontró cinco puntos que dependen del motor y que esta fase debe resolver o comprobar:

- la exclusión entre procesos que impide preparar dos veces la misma vista del borrador;
- la cola del procesamiento, que reparte documentos entre varios procesos sin repetir ninguno;
- el número de kardex único solo entre kardex activos;
- los datos estructurados de cada corrida (entradas, presentación, correcciones, calidad de lectura);
- la actividad por semana del Inicio, que empieza en lunes.

Como el ERP aún no está desplegado (F8), no hay datos que trasladar: se cambia el motor antes de la puesta en producción.

## Clarifications

### Session 2026-10-24

- Q: ¿Con qué credencial se conecta el ERP a su base en el SQL Server de la notaría? → A: con un login propio de SQL Server (usuario y clave de SQL Server, solo para el ERP); la clave se guarda fuera del repositorio, en el entorno del servidor.
- Q: ¿Qué edición de SQL Server 2016 tiene el servidor SQLSERVER? → A: el usuario no lo sabe todavía; se asume Standard y la guía de instalación la confirma antes de crear la base.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El personal trabaja igual que hoy (Priority: P1)

Las usuarias y el administrador entran al ERP, crean kardex y transferencias vehiculares, cargan documentos, ven la confrontación, aplican correcciones, descargan el informe y consultan el Inicio. Todo se comporta exactamente como con la base anterior.

**Why this priority**: es el objetivo de la fase. Si una pantalla o un resultado cambia, el cambio de motor es un defecto.

**Independent Test**: ejecutar la suite completa de pruebas y la medición del expediente de referencia contra la base nueva, y recorrer las pantallas principales con datos ficticios.

**Acceptance Scenarios**:

1. **Given** la base nueva vacía y migrada, **When** se ejecuta la suite de pruebas, **Then** pasan las mismas pruebas que pasan hoy.
2. **Given** el expediente de referencia, **When** se confronta cinco veces sobre la base nueva, **Then** el resultado es 8 de 8 errores, 0 falsos positivos y la misma salida en las cinco corridas.
3. **Given** un kardex activo «K-100», **When** se intenta crear otro kardex activo «K-100», **Then** se rechaza con el mismo mensaje de hoy; **And** si el primero se archiva, el número se puede reutilizar.
4. **Given** un kardex activo «K-100», **When** se crea «k-100», **Then** el ERP lo trata igual que hoy, es decir, como un número distinto (las mayúsculas cuentan).

---

### User Story 2 - El administrador de la notaría instala la base del ERP (Priority: P1)

El administrador de sistemas de la notaría crea en su SQL Server una base y un usuario exclusivos para el ERP, configura la conexión fuera del repositorio y deja el ERP funcionando, sin tocar las bases de sus otros sistemas.

**Why this priority**: sin esta guía no hay despliegue posible en F8.

**Independent Test**: seguir la guía en un SQL Server limpio y comprobar que el ERP arranca, migra la base y permite ingresar.

**Acceptance Scenarios**:

1. **Given** un SQL Server compatible, **When** el administrador sigue la guía, **Then** queda una base y un usuario propios del ERP, y el ERP arranca y aplica sus migraciones.
2. **Given** que falta la configuración de conexión o la clave, **When** se arranca el ERP, **Then** se niega a arrancar con un mensaje claro que no muestra la clave.
3. **Given** un SQL Server de versión no compatible, **When** el administrador prepara la base del ERP o verifica la instalación, **Then** el paso falla con un mensaje que dice qué versión se necesita, antes de que el ERP se use.
4. **Given** el usuario del ERP, **When** intenta leer o modificar una base de otro sistema de la notaría, **Then** no tiene permiso.

---

### User Story 3 - Varios procesos trabajan a la vez sin repetir trabajo (Priority: P2)

Mientras una usuaria navega, uno o más procesos en segundo plano leen documentos, confrontan y preparan la vista del borrador. Ningún documento se procesa dos veces y las pantallas no se quedan esperando a esos procesos.

**Why this priority**: es el comportamiento que hoy garantiza el motor anterior y que cambia con el nuevo.

**Independent Test**: lanzar dos procesos de extracción sobre una cola con varios documentos y navegar a la vez por la lista y por la confrontación.

**Acceptance Scenarios**:

1. **Given** cinco documentos pendientes y dos procesos de extracción, **When** terminan, **Then** cada documento se procesó una sola vez.
2. **Given** dos procesos que piden la misma vista del borrador, **When** corren a la vez, **Then** solo uno la prepara; **And** si ese proceso muere, la vista se puede volver a pedir sin intervención manual.
3. **Given** un proceso extrayendo un documento, **When** una usuaria abre la lista de kardex o el estado del kardex, **Then** la página responde sin esperar a que termine la extracción.
4. **Given** el proceso de extracción corriendo de forma continua, **When** SQL Server se reinicia o la conexión se corta, **Then** el proceso retoma la cola cuando el servidor vuelve, sin que nadie lo reinicie.

---

### User Story 4 - El CI prueba cada cambio contra SQL Server (Priority: P2)

Cada Pull Request ejecuta las pruebas contra SQL Server, con los mismos controles que hoy (lint, pruebas, SonarQube, dependencias y secretos).

**Why this priority**: sin esto, un cambio futuro podría volver a depender del motor anterior sin que nadie lo note.

**Independent Test**: abrir un PR y comprobar que las pruebas corren contra SQL Server y que su resultado es obligatorio para mergear.

**Acceptance Scenarios**:

1. **Given** un PR, **When** corre el CI, **Then** las pruebas se ejecutan contra SQL Server y el resultado bloquea el merge si fallan.

---

### User Story 5 - La actividad semanal sigue empezando en lunes (Priority: P3)

El administrador ve la actividad por semana del Inicio con semanas de lunes a domingo, como hoy, sea cual sea el idioma o la configuración regional del SQL Server.

**Why this priority**: es un indicador visible del administrador, y el motor nuevo calcula el inicio de semana según su configuración.

**Independent Test**: registrar confrontaciones ficticias un domingo y un lunes y comprobar en qué semana cuenta cada una.

**Acceptance Scenarios**:

1. **Given** una confrontación el domingo y otra el lunes siguiente, **When** se ve la actividad por semana, **Then** cuentan en semanas distintas, y la del lunes abre la nueva semana.

---

### Edge Cases

- El SQL Server no responde al arrancar o se cae con el ERP en marcha: el ERP muestra el error genérico de hoy, sin trazas ni cadena de conexión, y se recupera solo cuando el servidor vuelve.
- Un proceso de extracción muere con un documento tomado: el documento vuelve a la cola tras el mismo tiempo de espera configurado de hoy.
- Textos extraídos muy largos (expedientes de cientos de páginas): se guardan completos, sin recorte.
- Nombres, direcciones y textos con tildes, «ñ» y comillas tipográficas se guardan y se recuperan sin cambios.
- Dos valores que solo difieren en mayúsculas o en tildes (número de kardex, usuario, hash) se distinguen como hoy.
- Fechas y horas: se guardan en UTC y se muestran en hora de Lima, como hoy.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El ERP DEBE guardar todos sus datos en una base propia del SQL Server de la notaría, sin usar PostgreSQL.
- **FR-002**: El comportamiento visible DEBE ser idéntico al de hoy: mismas pantallas, mensajes, reglas, resultados de confrontación, informes y cifras del Inicio.
- **FR-003**: Las comparaciones y la unicidad de textos DEBEN distinguir mayúsculas y tildes, como hoy (número de kardex, nombre de usuario, hashes).
- **FR-004**: El número de kardex DEBE seguir siendo único solo entre kardex activos.
- **FR-005**: Un documento pendiente DEBE ser tomado por un solo proceso de extracción aunque haya varios corriendo.
- **FR-006**: La preparación de la vista de un borrador y las demás tareas exclusivas DEBEN ejecutarse en un solo proceso a la vez; si ese proceso muere, la exclusión se libera sola.
- **FR-007**: Las páginas de consulta (lista, estado del kardex, confrontación, Inicio) NO DEBEN quedar bloqueadas mientras un proceso en segundo plano escribe.
- **FR-008**: La actividad por semana DEBE agrupar de lunes a domingo, en hora de Lima, sin depender del idioma ni de la configuración regional del SQL Server.
- **FR-009**: La conexión (servidor, base, usuario, clave y opciones) DEBE configurarse fuera del repositorio, como hoy; sin configuración completa, el ERP no arranca.
- **FR-010**: El ERP DEBE funcionar con SQL Server 2016, la versión del servidor SQLSERVER (respuesta del usuario, 2026-10-24), y con las versiones posteriores, para que la notaría pueda actualizar sin cambiar el ERP. Contra una versión anterior a 2016, la preparación de la base y la verificación de la instalación DEBEN fallar con un mensaje que diga la versión mínima.
- **FR-011**: El repositorio DEBE incluir una guía para que el administrador cree la base y el usuario del ERP y configure la conexión. Su primer paso confirma la versión y la edición del servidor; si es Express, la guía advierte el tope de 10 GB por base antes de continuar.
- **FR-012**: Las pruebas automáticas DEBEN correr contra SQL Server, en local y en el CI. La medición del expediente de referencia DEBE correr contra SQL Server solo en local: usa expedientes reales y está prohibida en el CI.
- **FR-013**: Las referencias operativas a PostgreSQL (dependencias, configuración de ejemplo, guías y CI) DEBEN retirarse o sustituirse; no se mantienen dos motores.

### Security Requirements

- **SR-001**: El ERP usa un usuario de SQL Server exclusivo, con permisos solo sobre su base y sin roles de servidor.
- **SR-002**: El ERP se autentica con un login propio de SQL Server (usuario y clave); la clave vive solo en el entorno del servidor, fuera del repositorio. No se usa autenticación de Windows.
- **SR-003**: La conexión entre el ERP y SQL Server va cifrada. Si el servidor usa un certificado propio de la LAN, la confianza en él se configura de forma explícita, nunca por defecto.
- **SR-004**: La clave y la cadena de conexión no aparecen en el repositorio, en logs, en mensajes de error ni en pantallas.
- **SR-005**: Los datos personales (texto extraído, observaciones, hashes) quedan solo en la base del ERP; sus respaldos siguen el principio IV y se definen en F8.
- **SR-006**: Las bases de los otros sistemas de la notaría no son accesibles con el usuario del ERP, ni la base del ERP con los usuarios de esos sistemas, salvo los administradores del servidor.

### UX Requirements (principio VIII)

- Ninguna pantalla cambia. Los textos siguen sin términos técnicos: un fallo de la base se muestra con el mensaje genérico de hoy, sin el nombre del motor ni detalles de la conexión.
- Los estados de procesamiento (pendiente, procesando, listo, error) siguen actualizándose en la página como hoy.

### Key Entities

- **Base del ERP**: base exclusiva del ERP en el SQL Server de la notaría; contiene cuentas, roles, kardex, documentos, texto extraído, corridas, decisiones de corrección y análisis de sentido. Mismo modelo de datos que hoy.
- **Usuario de la base**: identidad con la que el ERP se conecta; solo tiene permisos sobre la base del ERP.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de las pruebas automáticas que pasan hoy pasan también contra la base nueva, en el CI y en local.
- **SC-002**: La medición del expediente de referencia da 8 de 8 errores, 0 falsos positivos y salida idéntica en 5 corridas seguidas.
- **SC-003**: Con dos procesos de extracción y 20 documentos en cola, ningún documento se procesa dos veces en 10 ejecuciones seguidas.
- **SC-004**: Mientras se extrae un documento, abrir la lista de kardex, el estado de un kardex o el Inicio tarda menos de 2 segundos con 500 kardex ficticios.
- **SC-005**: Un administrador instala la base del ERP desde cero en menos de 30 minutos siguiendo solo la guía.
- **SC-006**: La actividad por semana coincide con semanas de lunes a domingo en el 100 % de los casos de prueba, con el SQL Server configurado en español y en inglés.

## Assumptions

- SQL Server 2016 llegó al fin de su soporte extendido el 2026-07-14: Microsoft ya no publica parches de seguridad salvo con Extended Security Updates (ESU) pagadas, hasta 2029. Mantenerlo, contratar ESU o actualizar el servidor es decisión de la notaría; el ERP no lo exige, pero queda listo para la actualización (FR-010).
- La edición de SQL Server 2016 no se conoce todavía; se asume Standard (sin tope práctico de tamaño). Si en la instalación resulta Express, el tope de 10 GB por base se revisa en F8 junto con el respaldo.
- No hay datos de producción que trasladar: el ERP se despliega por primera vez en F8. Los datos locales de desarrollo son ficticios y se descartan.
- Se mantiene un solo motor (SQL Server) en producción, desarrollo y CI; no se conserva compatibilidad con PostgreSQL.
- La notaría crea la base y el usuario del ERP en su servidor; el repositorio entrega la guía y el script.
- El servidor SQLSERVER ya tiene fijado el tope de memoria de SQL Server (F61 lo pide antes de activar la capa de sentido).
- El respaldo diario de la base del ERP se resuelve en F8 y puede usar los planes de mantenimiento que la notaría ya tiene en SQL Server.
- En los equipos de desarrollo sin SQL Server instalado, las pruebas locales se corren contra un SQL Server de desarrollo (instalado o en contenedor); el CI usa un contenedor.
- `TODO(DESPLIEGUE)` de la constitución (VM Ubuntu + Docker o Windows nativo) sigue abierto para F8; esta fase no lo decide.
