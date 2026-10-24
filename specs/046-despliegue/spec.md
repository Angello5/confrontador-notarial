# Feature Specification: F8 · Despliegue en el servidor de la notaría

**Feature Branch**: `feat/f8-despliegue`

**Created**: 2026-10-24

**Status**: Código, scripts y pruebas implementados en `feat/f8-implementacion`. Pendientes las validaciones en un servidor de prueba de la notaría (T010, T017, T021, T023–T025, T028).

**Input**: User description: "El ERP debe quedar instalado y funcionando en el servidor SQLSERVER (Windows Server 2019) junto a su SQL Server 2016, dentro de la LAN y sin internet en ejecución. Las usuarias entran desde sus PC con el navegador, sin instalar nada, por HTTPS con un nombre interno; la web y el worker corren como servicios que arrancan con el servidor y se recuperan solos; respaldo diario de la base del ERP y de los originales, con restauración probada. Recomendación: Windows nativo, sin VM ni Docker."

## Origen

F8 es la fase de despliegue del roadmap: «funciona en el Windows Server, con respaldo diario». La constitución dejó abierto el mecanismo (`TODO(DESPLIEGUE)`: VM Ubuntu + Docker o Windows nativo), y el diagrama C4 de `docs/arquitectura/` todavía dibuja una VM Ubuntu con Docker.

El 2026-10-24 el usuario pidió preparar la spec recomendando **Windows nativo**:

- el servidor ya ejecuta SQL Server en Windows (F63);
- el equipo de sistemas de la notaría administra Windows;
- Docker en Windows exige WSL o Hyper-V, una capa más que mantener.

El servidor es SQLSERVER: Windows Server 2019, Xeon Bronze 3204 de 6 núcleos, 64 GB de memoria, sin GPU. NREAESGA (Windows Server 2012 R2) queda descartado por estar fuera de soporte. El ERP comparte la máquina con el SQL Server 2016 de la notaría y con sus otros sistemas.

Hoy el ERP solo corre en modo de desarrollo. Fuera de ese modo, las cookies de sesión exigen HTTPS, así que sin un certificado nadie podría iniciar sesión.

## Clarifications

### Session 2026-10-24

- Q: ¿Cuántos días se conservan los respaldos y dónde se guardan? → A: 30 días en otro disco del servidor, además del plan de respaldo de SQL Server de la notaría si lo tiene.
- Q: ¿De dónde sale el certificado HTTPS? → A: de la autoridad de certificados del dominio de Windows de la notaría.
- Q: ¿Se adopta Windows nativo, sin máquina virtual ni Docker, como mecanismo de despliegue? → A: sí; cierra `TODO(DESPLIEGUE)` de la constitución.
- Q: ¿Quién aplicará las actualizaciones del ERP en el servidor? → A: el desarrollador, por un acceso remoto (VPN o escritorio remoto) que habilita la notaría.
- Q: ¿Cómo se entera alguien de que algo falló en el servidor? → A: con un aviso en el Inicio del rol Administrador del ERP, y además en el Visor de eventos de Windows.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Las usuarias entran desde sus PC (Priority: P1)

Una usuaria abre el navegador en su PC de la notaría, escribe la dirección interna del ERP, ingresa con su cuenta y trabaja como siempre: crea kardex, sube documentos, ve la confrontación y descarga el informe. No instala nada en su PC.

**Why this priority**: es el propósito del despliegue; sin esto, el ERP no sirve a la notaría.

**Independent Test**: desde dos PC de la LAN distintas al servidor, ingresar y completar una confrontación con documentos ficticios.

**Acceptance Scenarios**:

1. **Given** el ERP instalado, **When** una usuaria abre la dirección interna en el navegador de su PC, **Then** ve la pantalla de ingreso por una conexión segura, sin avisos de certificado.
2. **Given** la usuaria escribe la dirección sin «https», **When** la abre, **Then** llega a la versión segura.
3. **Given** una PC fuera de la red de la notaría, **When** intenta abrir el ERP, **Then** no lo alcanza.
4. **Given** una usuaria con sesión iniciada, **When** sube un borrador y sus recaudos, **Then** ve el avance, la confrontación y puede descargar el informe, igual que en desarrollo.

---

### User Story 2 - El ERP se mantiene en marcha solo (Priority: P1)

La web y el procesamiento de documentos arrancan solos cuando se enciende el servidor, sin que nadie inicie sesión en él, y vuelven solos si se detienen por un fallo.

**Why this priority**: si un reinicio del servidor deja el ERP caído o los documentos en «Pendiente», la notaría deja de confiar en él.

**Independent Test**: reiniciar el servidor y, en otra prueba, detener a la fuerza cada proceso; comprobar que el ERP vuelve y que los documentos pendientes se procesan.

**Acceptance Scenarios**:

1. **Given** el servidor reiniciado, **When** termina de arrancar, **Then** el ERP responde y procesa documentos sin que nadie haga nada.
2. **Given** el procesamiento de documentos se detiene por un fallo, **When** pasa el tiempo de recuperación, **Then** vuelve solo y retoma la cola.
3. **Given** un documento que se estaba procesando cuando se cortó la luz, **When** el ERP vuelve, **Then** el documento vuelve a la cola y se procesa, como hoy.

---

### User Story 3 - Respaldo diario y restauración probada (Priority: P1)

Cada día se respalda la base del ERP y los borradores originales que el ERP conserva (F21). El administrador puede devolver el ERP al estado de un día anterior siguiendo un procedimiento que ya se probó.

**Why this priority**: el roadmap y el contrato exigen respaldo diario; un respaldo que nunca se restauró no garantiza nada.

**Independent Test**: tras un día de uso con datos ficticios, restaurar el respaldo en una base aparte y comprobar que kardex, confrontaciones y originales coinciden.

**Acceptance Scenarios**:

1. **Given** el ERP en uso, **When** pasa un día, **Then** existe un respaldo completo de ese día (base y originales) en el destino acordado.
2. **Given** un respaldo de un día anterior, **When** el administrador sigue el procedimiento de restauración, **Then** el ERP vuelve a ese estado y los originales coinciden con sus huellas.
3. **Given** que un respaldo falla, **When** el administrador revisa el servidor, **Then** encuentra el aviso del fallo sin datos personales.

---

### User Story 4 - El desarrollador instala y actualiza a distancia siguiendo una guía (Priority: P2)

El desarrollador se conecta al servidor por el acceso remoto que habilita la notaría, instala el ERP desde cero y luego lo actualiza a versiones nuevas, siguiendo solo la guía del repositorio. Si una actualización falla, vuelve a la versión anterior.

**Why this priority**: el ERP se actualiza a menudo (una fase por PR); cada actualización debe ser rutinaria, reversible y hecha sin ir a la notaría.

**Independent Test**: en un servidor de prueba, por acceso remoto, instalar desde cero y aplicar dos actualizaciones, una de ellas revertida.

**Acceptance Scenarios**:

1. **Given** un servidor con SQL Server y la base del ERP creada (F63), **When** el desarrollador sigue la guía por acceso remoto, **Then** el ERP queda accesible desde las PC.
2. **Given** una versión nueva, **When** el desarrollador la aplica, **Then** el ERP vuelve en minutos con los cambios y sin perder datos.
3. **Given** una actualización que falla, **When** el desarrollador sigue el paso de vuelta atrás, **Then** el ERP queda en la versión anterior y funcionando.
4. **Given** que el acceso remoto se corta a mitad de una actualización, **When** el administrador de la notaría reinicia el servidor, **Then** el ERP arranca en la versión anterior o en la nueva completa, nunca a medias.

---

### User Story 5 - Funciona sin internet (Priority: P2)

Todo lo que el ERP necesita en ejecución está en el servidor: los modelos de OCR, el diccionario, LibreOffice y, si se activa, la capa de sentido. Ninguna función depende de internet.

**Why this priority**: lo exige la constitución (principio VI); además, los datos personales no deben salir de la notaría.

**Independent Test**: un día de operación con el servidor sin salida a internet, confrontando kardex ficticios de todos los formatos.

**Acceptance Scenarios**:

1. **Given** el servidor sin salida a internet, **When** se confronta un kardex con `.docx`, `.doc`, PDF escaneado e imágenes, **Then** todo se procesa y la vista del borrador se muestra.
2. **Given** un recurso (modelo o diccionario) alterado o ausente, **When** se verifica la instalación, **Then** la verificación lo señala antes de usar el ERP.

---

### User Story 6 - Mantenimiento diario sin intervención (Priority: P3)

Cada día se limpian los archivos temporales vencidos, y los registros del ERP rotan sin crecer sin límite ni guardar datos personales.

**Why this priority**: evita que el disco se llene y cumple el principio IV (temporales y registros).

**Independent Test**: tras varios días de operación simulada, comprobar que no quedan temporales de más de 24 horas y que los registros están acotados y sin datos personales.

**Acceptance Scenarios**:

1. **Given** temporales con más de 24 horas, **When** corre el mantenimiento diario, **Then** se borran.
2. **Given** semanas de operación, **When** se revisan los registros, **Then** ocupan un tamaño acotado y no contienen DNI, nombres ni texto de documentos.

---

### Edge Cases

- El certificado vence: el aviso de FR-017 aparece 30 días antes, con tiempo para renovarlo antes de que las usuarias vean errores.
- SQL Server no está disponible al arrancar el servidor: el ERP espera y se conecta cuando la base vuelve, sin quedar caído.
- El disco se llena: el ERP no corrompe datos; los respaldos y temporales no compiten sin control por el espacio.
- Alguien entra por la IP en lugar del nombre: solo responden las direcciones configuradas.
- Una actualización con migraciones de base: se respalda la base antes de migrar.
- Cortes de luz: los documentos en proceso vuelven a la cola (tiempo de espera de hoy).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Las usuarias DEBEN usar el ERP desde el navegador de sus PC en la LAN, sin instalar nada en ellas.
- **FR-002**: El ERP DEBE servirse solo por HTTPS, con el nombre interno que defina la notaría; un acceso por HTTP DEBE llevar a HTTPS.
- **FR-003**: El ERP DEBE ejecutarse de forma nativa en Windows Server, en el servidor SQLSERVER, sin máquina virtual ni contenedores (resuelve `TODO(DESPLIEGUE)` de la constitución).
- **FR-004**: La web y el procesamiento de documentos DEBEN arrancar con el servidor, sin sesión iniciada, y reiniciarse solos tras un fallo.
- **FR-005**: El procesamiento de documentos DEBE comunicarse con la web solo por la cola en la base (como hoy).
- **FR-006**: Ninguna función del ERP DEBE depender de internet en ejecución. Los recursos (modelos de OCR, diccionario `es_PE`, LibreOffice y, si se activa, la capa de sentido) se instalan y verifican en el despliegue.
- **FR-007**: La base del ERP y los borradores originales DEBEN respaldarse cada día en **otro disco del servidor**, conservando **30 días**; el respaldo del día 31 se borra solo. Si la notaría tiene un plan de respaldo de SQL Server, la base del ERP se incluye también en él.
- **FR-008**: DEBE existir un procedimiento de restauración probado en la instalación, que devuelva el ERP al estado de un día anterior.
- **FR-009**: Los temporales vencidos DEBEN limpiarse cada día de forma automática.
- **FR-010**: El repositorio DEBE incluir una guía de instalación desde cero, de actualización y de vuelta atrás. Antes de aplicar migraciones, la actualización respalda la base.
- **FR-011**: En producción, el modo de desarrollo DEBE estar apagado, y las claves (clave secreta del ERP y clave de la base) DEBEN vivir solo en el servidor, con acceso restringido.
- **FR-012**: Los registros del ERP DEBEN rotar con un tamaño acotado y no DEBEN contener datos personales ni contenido de documentos.
- **FR-013**: El ERP DEBE convivir con SQL Server y los otros sistemas del servidor sin quitarles recursos: memoria y núcleos acotados y documentados.
- **FR-014**: El nombre y el logo de la notaría DEBEN configurarse en el servidor, sin escribirse en el repositorio.
- **FR-015**: El administrador DEBE poder comprobar en un paso que la web, el procesamiento, la base y los recursos están bien.
- **FR-016**: El diagrama de arquitectura de despliegue DEBE reflejar la instalación nativa en Windows.
- **FR-017**: El Inicio del rol Administrador DEBE mostrar un aviso, y el servidor DEBE registrar el mismo hecho en el Visor de eventos de Windows, cuando:
  - el último respaldo correcto tiene más de 26 horas;
  - el certificado HTTPS vence en 30 días o menos;
  - el procesamiento de documentos lleva más de 10 minutos sin dar señales de actividad.

  El aviso desaparece solo cuando la causa se resuelve.

### Security Requirements

- **SR-001**: El certificado HTTPS lo emite la **autoridad de certificados del dominio de Windows de la notaría**, para el nombre interno del ERP; las PC del dominio ya confían en ella y no muestran avisos. Su renovación sigue el procedimiento de esa autoridad.
- **SR-002**: Solo el puerto HTTPS del ERP queda abierto, y solo hacia la LAN. El puerto de SQL Server no se abre a las PC por el ERP. Nada del ERP se expone a internet.
- **SR-003**: Los servicios del ERP corren con una cuenta de Windows propia, sin privilegios de administrador, con escritura solo en sus carpetas (temporales, originales, registros).
- **SR-004**: Las claves no aparecen en el repositorio, en registros, en mensajes de error ni en la línea de comandos de los procesos.
- **SR-005**: Los respaldos contienen datos personales (Ley 29733): solo los administradores pueden leerlos, y no se copian fuera de la notaría sin su decisión.
- **SR-006**: Las sesiones viajan solo por la conexión segura, con las protecciones de cookies de hoy.
- **SR-007**: El acceso remoto del desarrollador lo habilita y controla la notaría: VPN o escritorio remoto detrás de VPN (nunca expuesto directo a internet), con una cuenta nominal del desarrollador, sin compartir credenciales. Los datos personales no se copian fuera del servidor durante el mantenimiento.

### UX Requirements (principio VIII)

- La única pantalla que cambia es el Inicio del rol Administrador, que suma los avisos de FR-017. Usan el mismo componente de aviso del Inicio (consistencia, heurística 4) y dicen en lenguaje llano qué pasa y qué hacer, por ejemplo: «El respaldo de anoche no se completó. Avise al encargado de sistemas.» Nunca muestran rutas, comandos ni nombres técnicos (heurísticas 2 y 9).
- El Inicio de las usuarias no cambia.
- Si el ERP se está actualizando o no puede conectar con la base, la usuaria ve un mensaje claro en español, sin trazas técnicas, que le dice que intente en unos minutos.

### Key Entities

- **Servicio web**: atiende a las usuarias por HTTPS en el servidor.
- **Servicio de procesamiento**: el worker; toma documentos de la cola en la base y guarda resultados.
- **Tarea diaria**: limpieza de temporales y respaldo.
- **Respaldo**: copia diaria de la base del ERP y de los originales, con fecha, destino y retención.
- **Cuenta de servicio**: identidad de Windows con la que corren los servicios.
- **Estado del sistema**: último respaldo correcto, vencimiento del certificado y última señal de actividad del procesamiento; alimenta los avisos de FR-017.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Desde 2 PC de la LAN distintas, una usuaria ingresa y completa una confrontación sin instalar nada y sin avisos de certificado.
- **SC-002**: Tras reiniciar el servidor, el ERP atiende y procesa documentos en menos de 5 minutos sin intervención.
- **SC-003**: Si el procesamiento de documentos se detiene por un fallo, vuelve en menos de 2 minutos y procesa los pendientes.
- **SC-004**: Durante 7 días seguidos existe un respaldo de cada día, y una restauración de prueba devuelve el ERP a un día anterior en menos de 1 hora.
- **SC-005**: Por acceso remoto, el desarrollador instala el ERP desde cero en menos de 2 horas (sin contar descargas) y aplica una actualización en menos de 15 minutos, siguiendo solo la guía.
- **SC-006**: Con 10 usuarias a la vez, las pantallas habituales responden en menos de 2 segundos.
- **SC-007**: En un día completo de operación, el ERP no intenta ninguna conexión a internet.
- **SC-008**: Al simular cada uno de los tres fallos de FR-017, el aviso aparece en el Inicio del Administrador y en el Visor de eventos en menos de 15 minutos, y desaparece al corregir la causa.

## Assumptions

- Windows nativo es decisión del usuario (2026-10-24) y cierra `TODO(DESPLIEGUE)` con una enmienda de la constitución en esta misma rama.
- La base y el login del ERP ya existen en SQL Server (F63, `scripts/sqlserver/crear_base.sql`).
- El nombre interno de acceso (por ejemplo `erp.notaria.local`) y su registro en el DNS de la notaría los define y crea su administrador; el ERP lo recibe por configuración.
- Las PC usan un navegador actual (Edge o Chrome) y están en la misma LAN que el servidor.
- El procesamiento corre un documento a la vez, como hoy; varios procesos en paralelo quedan fuera del alcance.
- La capa de sentido (F61) se instala apagada; activarla sigue su propia guía (`specs/043-capa-sentido/quickstart.md`).
- El tope de memoria de SQL Server lo fija el administrador de la notaría (como pide F61).
- Las actualizaciones se aplican fuera del horario de atención.
- La notaría provee el acceso remoto (VPN o escritorio remoto detrás de VPN) y una cuenta nominal para el desarrollador en el servidor; el ERP no instala ni abre ningún acceso remoto propio.
