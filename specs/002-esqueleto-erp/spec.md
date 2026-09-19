# Feature Specification: F2 · Esqueleto del ERP

**Feature Branch**: `feature/f2-esqueleto`

**Created**: 2026-09-18

**Status**: Draft

**Input**: User description: "Los usuarios de la notaría inician sesión y ven un layout con menú lateral cuyas opciones dependen de su rol. Un administrador crea y desactiva usuarios y les asigna rol. Sin funcionalidad de negocio todavía."

## Clarifications

### Session 2026-09-18

- Q: ¿Qué roles existen? → A: Existen exactamente dos roles: Administrador y Usuario.
- Q: ¿Qué credenciales recibe una cuenta nueva y cuándo debe cambiarlas? → A: El administrador crea la cuenta con un nombre de usuario y una clave temporal; el cambio de clave es obligatorio en el primer ingreso. No se usa correo.
- Q: ¿Qué ocurre con las sesiones y la reactivación al desactivar una cuenta? → A: Se revocan todas sus sesiones al instante y el administrador puede reactivar la cuenta.
- Q: ¿Dónde se administran las cuentas y cómo se crea el primer administrador? → A: La gestión de usuarios y roles se realiza en Django admin (`/admin`), sin pantallas propias ni asistente de primer uso. El primer administrador se crea con un comando de gestión en el servidor.
- Q: ¿Qué límites se aplican al desactivar cuentas de administradores? → A: Nadie puede desactivarse a sí mismo ni dejar el sistema sin ningún administrador activo.
- Q: ¿Qué ocurre tras varios intentos de ingreso fallidos? → A: Tras cinco intentos consecutivos para una misma cuenta, se rechaza el ingreso durante 15 minutos con el mismo mensaje genérico; el estado queda en la base de datos, se reinicia al ingresar correctamente y un Administrador puede desbloquear la cuenta desde `/admin`.
- Q: ¿Puede un Administrador asignar una clave temporal desde el cambio de clave del admin? → A: Sí. El cambio fija `force_password_change=true` e incrementa `session_version` para revocar las sesiones abiertas de la cuenta.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ingresar al ERP (Priority: P1)

Como usuario de la notaría, quiero iniciar sesión y ver la estructura principal del ERP para acceder a las funciones que me corresponden.

**Why this priority**: El acceso autenticado y el esqueleto de navegación son la base visible de F2.

**Independent Test**: Intentar ingresar con una cuenta habilitada y con una cuenta deshabilitada; comprobar el resultado y el contenido de navegación permitido.

**Acceptance Scenarios**:

1. **Given** una cuenta habilitada, **When** su titular inicia sesión correctamente, **Then** ve el layout del ERP y las opciones autorizadas para sus roles.
2. **Given** una persona sin sesión, **When** intenta abrir una pantalla protegida, **Then** se le solicita iniciar sesión y no se muestra contenido protegido.
3. **Given** una cuenta deshabilitada, **When** su titular intenta iniciar sesión, **Then** se rechaza el acceso y se muestra un mensaje claro que no revela información sensible.
4. **Given** un usuario autenticado, **When** intenta acceder directamente a una función que su rol no autoriza, **Then** se deniega el acceso aunque conozca la dirección de la pantalla.

### User Story 2 - Administrar cuentas (Priority: P1)

Como administrador, quiero crear, desactivar y reactivar cuentas y asignarles un rol desde `/admin` para controlar quién puede usar el ERP.

**Why this priority**: La notaría necesita administrar el acceso antes de habilitar funciones posteriores.

**Independent Test**: Crear una cuenta ficticia, asignarle un rol, verificar el acceso que corresponde y desactivarla para comprobar que deja de ingresar.

**Acceptance Scenarios**:

1. **Given** un administrador autenticado en `/admin`, **When** crea una cuenta con nombre de usuario, clave temporal y uno de los dos roles, **Then** la cuenta queda activa y debe cambiar la clave en el primer ingreso.
2. **Given** un administrador autenticado en `/admin`, **When** desactiva una cuenta, **Then** se revocan al instante todas sus sesiones y la cuenta no puede iniciar sesión.
3. **Given** un administrador autenticado en `/admin`, **When** reactiva una cuenta, **Then** la cuenta puede volver a iniciar sesión.
4. **Given** un usuario que no tiene permiso administrativo, **When** intenta crear, desactivar, reactivar o cambiar el rol de una cuenta, **Then** la operación se deniega y no modifica cuentas.
5. **Given** una acción administrativa que desactivaría al propio administrador o dejaría cero administradores activos, **When** intenta confirmarla, **Then** la operación se deniega.
6. **Given** una acción administrativa confirmada, **When** termina, **Then** la interfaz informa el resultado sin exponer datos personales en mensajes o registros.
7. **Given** cinco intentos fallidos consecutivos para una cuenta, **When** se intenta ingresar durante los siguientes 15 minutos desde cualquier punto de autenticación, **Then** se rechaza con el mismo mensaje genérico que para una cuenta inexistente y solo un Administrador puede desbloquearla desde `/admin`.

### Edge Cases

- Una sesión revocada por desactivación no puede reutilizarse en solicitudes posteriores.
- La última cuenta Administrador activa no puede desactivarse; tampoco puede desactivarse a sí misma aunque exista otro administrador.
- El nombre de usuario o identificador de una cuenta ya está asignado: mostrar un error entendible sin revelar datos de otra cuenta.
- Una petición directa o manipulada intenta asignar un rol no permitido al administrador que la ejecuta: denegarla en el servidor.
- Una pantalla no tiene opciones habilitadas para el rol: mostrar un estado vacío comprensible y no aparentar un error.
- El bloqueo temporal y los intentos concurrentes se almacenan en la base de datos; el proceso no depende de una caché en memoria.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir que una persona con cuenta habilitada se autentique antes de ver contenido interno.
- **FR-002**: El sistema MUST impedir el inicio de sesión de cuentas desactivadas.
- **FR-003**: El sistema MUST presentar a cada persona autenticada un layout principal con navegación lateral.
- **FR-004**: En F2, ambos roles MUST ver la opción «Inicio»; solo Administrador MUST ver la opción «Administración» que enlaza al Django admin. Las opciones visibles MUST corresponder a los permisos del rol asignado; la autorización MUST comprobarse también en el servidor en cada acción protegida.
- **FR-005**: Un Administrador MUST poder crear cuentas con nombre de usuario y clave temporal, asignar exactamente uno de los roles Administrador o Usuario, desactivar y reactivar cuentas desde el Django admin nativo en `/admin`; no habrá pantallas propias de gestión ni asistente de primer uso.
- **FR-006**: Una cuenta creada con clave temporal MUST cambiarla obligatoriamente en su primer ingreso; no se utilizará correo para crear o recuperar la cuenta en F2.
- **FR-007**: Solo una persona con rol Administrador MUST poder gestionar cuentas y roles. Una cuenta Usuario MUST poder acceder solo a las funciones autorizadas para ese rol.
- **FR-008**: Desactivar una cuenta MUST revocar todas sus sesiones al instante e impedir nuevos inicios de sesión; un Administrador MUST poder reactivarla.
- **FR-009**: El sistema MUST denegar la desactivación de la propia cuenta por quien la ejecuta y toda acción que deje cero cuentas Administrador activas.
- **FR-012**: El primer Administrador MUST aprovisionarse mediante un comando de gestión ejecutado en el servidor.
- **FR-013**: Tras cinco intentos fallidos consecutivos para una cuenta existente, el backend de autenticación MUST rechazar su ingreso durante 15 minutos con el mismo mensaje genérico usado para credenciales inválidas; el bloqueo MUST persistir en la base de datos, cubrir toda autenticación incluida `/admin`, reiniciarse al ingresar correctamente y poder ser retirado por un Administrador desde `/admin`. El intento de una cuenta inexistente MUST conservar una respuesta genérica sin revelar existencia o bloqueo.
- **FR-014**: El bloqueo MUST aplicar al usuario identificado por las credenciales, contar intentos concurrentes sin perder incrementos y permitir al Administrador desbloquear la cuenta desde su formulario en `/admin`.
- **FR-015**: El cambio de clave de una cuenta realizado por un Administrador desde `/admin` MUST marcar la cuenta para cambio obligatorio e invalidar sus sesiones abiertas inmediatamente.
- **FR-010**: F2 MUST limitarse a autenticación, layout y navegación, y administración de cuentas y roles; no incluye expedientes, carga o procesamiento de archivos, confrontación, observaciones, informes ni otras funciones de negocio.
- **FR-011**: El sistema MUST funcionar dentro de la LAN sin depender de servicios externos disponibles en tiempo de ejecución.

### Requisitos de seguridad y privacidad (Constitución VI)

- **SEC-001**: Toda pantalla y acción interna MUST requerir autenticación; cada acción protegida MUST exigir autorización explícita acorde con el rol. Ocultar una opción del menú no sustituye la autorización del servidor.
- **SEC-002**: Solo Administradores autorizados MUST poder crear cuentas, desactivarlas, reactivarlas o asignar roles desde `/admin`. Las solicitudes manipuladas o directas también se deniegan.
- **SEC-003**: Las cuentas desactivadas MUST quedar impedidas de iniciar sesión y todas sus sesiones MUST revocarse al instante; Administradores pueden reactivarlas. Nadie puede desactivarse a sí mismo ni dejar cero Administradores activos.
- **SEC-008**: Los intentos fallidos y el vencimiento del bloqueo MUST persistirse en PostgreSQL, sin caché en proceso; los mensajes visibles MUST ser idénticos para credenciales incorrectas, cuenta inexistente y cuenta bloqueada.
- **SEC-004**: La interfaz, errores y registros MUST evitar contraseñas, secretos, tokens y datos personales innecesarios; no se incluirán datos reales en pruebas, fixtures, ejemplos ni mensajes.
- **SEC-005**: El sistema MUST usar autenticación de Django y permisos asociados a los grupos Administrador y Usuario. La gestión se realiza en Django admin (`/admin`); el primer Administrador se crea con un comando de gestión en el servidor.
- **SEC-006**: El acceso al ERP MUST operar sin llamadas a modelos de lenguaje ni servicios de IA.
- **SEC-007**: Las cookies de sesión y CSRF MUST usar el atributo Secure cuando DEBUG está desactivado. El despliegue HTTPS interno se confirmará en F8.

### Requisitos de usabilidad y accesibilidad (Constitución VIII)

- **UX-001 · Visibilidad del estado**: las pantallas propias de login, cambio obligatorio de clave y layout MUST confirmar cada acción; cualquier proceso que exceda 1 segundo MUST mostrar si está pendiente, en curso, completado o fallido.
- **UX-002 · Lenguaje del trabajo**: pantallas, etiquetas y mensajes MUST estar en español y usar vocabulario comprensible para la notaría; no mostrar términos internos como “task”, “hash” o “worker”.
- **UX-003 · Control y libertad**: la persona MUST contar con una forma clara de volver atrás; una operación en curso MUST poder cancelarse cuando exista una operación cancelable en el alcance.
- **UX-004 · Consistencia**: en login, cambio obligatorio de clave y layout del ERP, los controles que cumplen la misma función MUST mantener presentación, ubicación y comportamiento consistentes. La gestión de cuentas usa el Django admin nativo.
- **UX-005 · Prevención de errores**: los campos obligatorios MUST validarse antes de guardar; una acción destructiva o irreversible MUST pedir confirmación antes de ejecutarse.
- **UX-006 · Reconocimiento**: el menú MUST mostrar opciones según permisos; las pantallas MUST indicar dónde está la persona mediante navegación visible y no exigir recordar datos entre pantallas.
- **UX-007 · Flexibilidad y eficiencia**: las listas de cuentas MUST permitir localizar una cuenta; filtros o atajos adicionales quedan sujetos a que el flujo y volumen definidos por la notaría los justifiquen.
- **UX-008 · Diseño minimalista**: cada pantalla MUST mostrar solo controles e información necesarios para la tarea disponible en F2.
- **UX-009 · Recuperación de errores**: los mensajes MUST explicar en lenguaje claro qué ocurrió y qué puede hacer la persona, sin trazas técnicas ni datos personales.
- **UX-010 · Ayuda**: los campos de login y cambio obligatorio de clave que requieran explicación MUST incluir ayuda breve y estos flujos MUST contar con una guía de uso.
- **A11Y-001**: Todo campo MUST tener etiqueta; la navegación MUST poder realizarse con teclado, el foco MUST ser visible y el contraste MUST ser suficiente para leer y distinguir controles.

### Key Entities *(include if feature involves data)*

- **Cuenta de usuario**: identidad activa o desactivada identificada por nombre de usuario, con clave temporal inicial y cambio obligatorio en el primer ingreso; la desactivación revoca sus sesiones.
- **Rol**: uno de exactamente dos grupos asignables, Administrador o Usuario, que define permisos y opciones de navegación.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de las pantallas internas requiere una sesión válida, y el 100 % de las acciones protegidas rechaza solicitudes sin permiso.
- **SC-002**: El 100 % de las cuentas desactivadas es rechazado al iniciar sesión.
- **SC-003**: Administrador ve «Inicio» y «Administración»; Usuario ve solo «Inicio». Ningún acceso denegado depende únicamente de ocultar una opción.
- **SC-004**: El 100 % de las acciones de administración de cuentas en `/admin` requiere permiso de Administrador; el 100 % de las desactivaciones revoca sesiones y ninguna permite desactivar al propio operador ni al último Administrador activo.
- **SC-008**: El 100 % de las cuentas nuevas exige cambio de clave temporal en su primer ingreso, sin requerir correo.
- **SC-009**: La quinta falla consecutiva bloquea la cuenta por 15 minutos en el backend compartido (incluido `/admin`), sin perder incrementos concurrentes y con la misma respuesta genérica que para una cuenta inexistente.
- **SC-010**: El 100 % de las claves asignadas por un Administrador desde `/admin` obliga a un nuevo cambio y revoca las sesiones existentes de la cuenta.
- **SC-005**: El 100 % de los campos visibles tiene etiqueta y se puede recorrer usando teclado con foco visible.
- **SC-006**: La revisión de las pantallas de F2 cubre explícitamente las diez heurísticas de Nielsen y los mínimos de accesibilidad definidos en los requisitos UX y A11Y.
- **SC-007**: La revisión de F2 encuentra cero datos personales reales, secretos o llamadas a servicios de IA en el material de la funcionalidad.

## Assumptions

- F2 corresponde exclusivamente a la fase “Esqueleto del ERP” del roadmap; no implementa reglas de negocio ni flujos de expedientes.
- La constitución establece autenticación de Django y exactamente dos roles; las pantallas propias de F2 son login, cambio obligatorio de clave y layout con navegación según rol.
- Las pruebas y demostraciones usan únicamente cuentas y datos ficticios.
- La administración de usuarios y roles usa Django admin nativo; F2 no incorpora pantallas propias de gestión ni asistente de primer uso.
