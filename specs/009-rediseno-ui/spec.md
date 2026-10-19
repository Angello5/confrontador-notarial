# Feature Specification: F14 · Rediseño de interfaz

**Feature Branch**: `feature/f14-rediseno-ui`

**Created**: 2026-09-27

**Status**: Implementado e integrado (PR #43)

**Input**: El propietario diseñó en Figma «Confrontador Notarial — ERP Dashboard» (9 pantallas) y pide que el ERP «sea de ese color, de manera similar». Las capturas de referencia viven fuera del repositorio en `~/pruebas-confrontador/figma/` (`s01-dashboard.png`, `s02-nueva-confrontacion.png`, `s03-shell-confrontacion.png`, `s04-admin-inicio.png`) y la estructura de capas de las 9 pantallas en `metadata.xml` del mismo directorio. No se versionan: llevan un nombre comercial y datos de maqueta.

## Principio

**Misma aplicación, misma información, mismos flujos: cambia la piel.** F14 no añade ni quita funciones. Todo lo que hoy se puede hacer (crear expediente, cargar por rol, sondeo de estado, confrontar, ver extracción y observaciones, eliminar documentos, administración) se sigue haciendo desde los mismos formularios, rutas y permisos. Lo que cambia es el aspecto: colores, jerarquía tipográfica, disposición y componentes visuales tomados del diseño.

## Clarifications

### Session 2026-09-27

- Q: El diseño «Confrontador integrado — Usuario» trae un interruptor «AI option». → A: **Se excluye.** La constitución prohíbe IA en el ERP. No se dibuja ni desactivado.
- Q: El diseño muestra «Tipo de acto», «Reportes», «Auditoría», «Configuración», «Buscar módulo…» y un filtro de estado. → A: Son de fases futuras (F6, F7, F9). **No se muestran** ni como enlaces inertes: el menú solo lista lo que existe.
- Q: ¿Tipografía? → A: El diseño usa una sans geométrica redondeada. El ERP corre en LAN sin Internet, así que **no se cargan fuentes remotas**. Se usa una pila de sistema (`system-ui, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`). Empaquetar una fuente libre queda como deuda si el propietario la pide.
- Q: ¿Se sustituye AdminLTE? → A: No. Se conserva AdminLTE 4 y Bootstrap 5 ya empaquetados; el diseño se aplica con **una hoja de estilos propia** (`static/css/erp.css`) que redefine variables de Bootstrap/AdminLTE y añade los componentes que faltan (chips de estado, tarjetas de métrica, riel de pasos, zona de arrastre). Sin dependencias nuevas ni herramientas de compilación.
- Q: ¿La marca? → A: Marca genérica del producto: círculo verde con iniciales «CN», nombre «CONFRONTADOR» y subtítulo «ERP NOTARIAL». No se usa el nombre de ninguna notaría real.
- Q: ¿Nombre del usuario en pantalla? → A: Nombre de usuario (`username`) y rol (Administrador / Usuario) en el pie del menú lateral, y sus iniciales en el avatar. Sin correo.

## Paleta y componentes (medidos sobre el diseño)

| Token | Valor | Uso |
|---|---|---|
| `--erp-navy` | `#0F2765` | Menú lateral, botón primario, tarjeta de acceso rápido, encabezados de tabla en tarjetas oscuras |
| `--erp-navy-2` | `#16326F` | Ítem activo del menú, hover del botón primario |
| `--erp-green` | `#44D880` | Acento: marca, indicador del ítem activo, botón «Comenzar»/«Confrontar» sobre fondo navy, paso completado |
| `--erp-bg` | `#F2F3F7` | Fondo de página |
| `--erp-surface` | `#FFFFFF` | Tarjetas |
| `--erp-border` | `#C3C9D9` | Borde de tarjetas y separadores |
| `--erp-ink` | `#00112C` | Texto principal |
| `--erp-muted` | `#5C6470` (el `#6C757D` de Bootstrap no llega a AA sobre `--erp-bg`) | Texto secundario, migas |
| `--erp-success-bg` | `#E5FAED` | Chip «Conforme/Listo», fila de archivo procesado, aviso de privacidad |
| Rojo de Bootstrap (`danger`) | — | Chip «Revisión/Error» sobre fondo rosado claro |

Componentes del diseño que se reproducen:

- **Shell**: menú lateral navy de 248 px con marca, etiqueta de sección en mayúsculas pequeñas, ítems con icono, ítem activo con fondo `navy-2` y barra verde a la izquierda, pie con usuario y rol. Barra superior blanca con botón de menú (solo móvil), migas de pan y avatar con iniciales; el botón «Cerrar sesión» se mantiene visible en la barra superior.
- **Cabecera de página**: «eyebrow» en mayúsculas pequeñas, título grande, subtítulo gris, acción primaria a la derecha.
- **Tarjeta de métrica**: etiqueta con punto de color, número grande, línea de apoyo.
- **Chip de estado**: píldora con fondo suave y texto en negrita (verde, rojo, gris, navy).
- **Tarjeta de acceso rápido**: fondo navy, eyebrow verde, título blanco, pasos numerados con círculo verde, botón verde.
- **Riel de pasos**: cuatro pasos con círculo y línea; completado en verde, actual en navy, pendiente en gris.
- **Zona de arrastre**: recuadro punteado sobre fondo `bg` con «+», título y ayuda de formatos; debajo, filas de archivo con ✓ verde y estado a la derecha.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reconocer el sistema de un vistazo (Priority: P1)

Como usuario de la notaría, quiero que todas las pantallas compartan el menú lateral navy, la marca y la cabecera del diseño, para orientarme igual en cualquier módulo.

**Independent Test**: Abrir Inicio, Expedientes, un expediente y su confrontación con un usuario y con un administrador; comparar con las capturas del diseño.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado con rol Usuario, **When** abre cualquier pantalla, **Then** ve el menú lateral con «Inicio» y «Expedientes», su nombre y rol en el pie, y el ítem de la pantalla actual resaltado con la barra verde.
2. **Given** un administrador, **When** abre cualquier pantalla, **Then** además ve la sección «Administración» con «Usuarios y permisos» hacia la administración de Django.
3. **Given** cualquier pantalla a 1024 px o menos de ancho, **When** pulsa el botón de menú, **Then** el menú lateral se despliega y se puede cerrar; el contenido no se desborda horizontalmente.

### User Story 2 - Inicio con el estado real del trabajo (Priority: P1)

> Reemplazado por F53 (`specs/041-inicio-administrador/`) en el Inicio del administrador y en el aviso de documentos ilegibles.

Como usuario, quiero que Inicio resuma mis expedientes con las tarjetas del diseño y me lleve al siguiente paso.

**Acceptance Scenarios**:

1. **Given** expedientes visibles para el usuario, **When** abre Inicio, **Then** ve cuatro tarjetas de métrica calculadas con datos reales: «Expedientes» (total visible), «Procesando» (con documentos pendientes o en proceso), «Listos para confrontar» (estado LISTO) y «Con error»; una tabla «Últimos expedientes» con los cinco más recientes (código, estado en chip, actualizado, abrir); y una tarjeta navy «Nueva confrontación» con los tres pasos (sube los documentos, procesa el expediente, revisa las observaciones) y botón verde hacia Expedientes.
2. **Given** un administrador, **When** abre Inicio, **Then** la tarjeta navy es «Control administrativo» con botón «Administrar» hacia la administración.
3. **Given** un usuario sin expedientes, **When** abre Inicio, **Then** las métricas muestran 0 y la tabla se sustituye por un texto de ayuda con enlace a crear el primero.

### User Story 3 - Expedientes como tabla del diseño (Priority: P2)

**Acceptance Scenarios**:

1. **Given** la lista de expedientes, **When** se abre, **Then** la cabecera muestra «Expedientes», subtítulo y el botón «+ Nuevo expediente», que despliega el formulario de código actual (mismo campo, misma validación) sin recargar; la tabla lista código, estado en chip, número de documentos, actualizado y «Abrir».
2. **Given** un error de validación del código, **When** se envía, **Then** el formulario queda visible con el error, como hoy.

### User Story 4 - Cargar y confrontar con el riel de pasos (Priority: P1)

**Acceptance Scenarios**:

1. **Given** un expediente, **When** se abre, **Then** la cabecera muestra el código, el riel «Fuentes → Borrador → Procesamiento → Resultado» con el paso actual derivado del estado (sin documentos → Fuentes; falta borrador o falta cliente/minuta → el que falte; pendientes o procesando → Procesamiento; todo listo → Resultado), el panel izquierdo «Documentos del expediente» con las zonas de arrastre de cliente y minuta, el panel derecho «Borrador a confrontar», la línea de privacidad («los archivos se procesan localmente y se eliminan al terminar; el texto extraído se conserva») y el botón navy «Confrontar borrador» por borrador, habilitado solo cuando el sondeo lo permite, como hoy.
2. **Given** archivos cargados, **When** se muestran, **Then** cada fila lleva chip con el texto de estado actual («Pendiente», «Procesando», «Listo» o «No se pudo procesar», FR-005) y ✓ verde cuando está lista, y el botón «Eliminar» con confirmación, como hoy.
3. **Given** el sondeo de estado, **When** cambia el estado, **Then** el riel y los chips se actualizan sin recargar, con la misma respuesta JSON de hoy (sin campos nuevos).

### User Story 5 - Resultado de la confrontación (Priority: P2)

**Acceptance Scenarios**:

1. **Given** un resultado, **When** se muestra, **Then** la cabecera dice «Resultado de la confrontación» con el código y el borrador; tres tarjetas de métrica con el número de observaciones de Personas, Regla y Ortografía; las tres tablas actuales con chip de tipo; y «Qué se extrajo de los documentos» sigue plegado con las tablas de F13 (Personas con ficha, Menciones sin ficha, Aporte por documento).
2. **Given** los estados NO_DISPONIBLE, ADVERTENCIA_CORRESPONDENCIA y ERROR_SEGURO, **When** se muestran, **Then** conservan su texto y su semántica (aviso, advertencia, error) con los colores de la paleta.

### User Story 6 - Ingreso (Priority: P3)

1. **Given** la pantalla de ingreso, **When** se abre, **Then** muestra la marca sobre fondo navy y la tarjeta blanca con el mismo formulario y mensajes de hoy.

## Requirements *(mandatory)*

- **FR-001**: Toda pantalla autenticada DEBE extender `core/base.html` con el shell del diseño (menú lateral navy, barra superior, migas, avatar, pie de usuario). El menú DEBE listar solo funciones existentes según rol.
- **FR-002**: Los estilos DEBEN vivir en `static/css/erp.css`, servido con `{% static %}`, con los tokens de la tabla como variables CSS y redefiniendo las variables de Bootstrap/AdminLTE necesarias. Sin CSS en línea salvo el que ya exige Alpine (`x-show`).
- **FR-003**: No se DEBEN añadir dependencias (JS, CSS, fuentes remotas, herramientas de compilación) ni migraciones. Alpine y AdminLTE se conservan tal cual.
- **FR-004**: Inicio DEBE calcular sus métricas y últimos expedientes con la misma visibilidad por usuario que la lista de expedientes (la consulta se reutiliza, no se duplica). El contexto no DEBE exponer texto extraído, hashes ni rutas.
- **FR-005**: Formularios, rutas, permisos, CSRF, sondeo JSON, mensajes y textos de estado DEBEN conservar su comportamiento; los tests existentes se adaptan solo en lo que cambia de marcado (títulos, clases, orden), nunca en lo que verifican.
- **FR-006**: Cada chip, tarjeta de métrica y paso del riel DEBE derivarse del estado que ya existe en el contexto (`resumen.estado`, estados de documento, disponibilidad de confrontación). No se inventan estados.
- **FR-007**: Accesibilidad: contraste AA en texto sobre navy y sobre verde (texto navy sobre botón verde; texto blanco sobre navy), foco visible, `aria-current` en el ítem activo, tablas con encabezados y `caption`, y el botón de menú con `aria-expanded`. El riel de pasos DEBE tener texto equivalente (`aria-label` o texto oculto).
- **FR-008**: Responsivo: correcto a 1440, 1024 y 390 px de ancho; el menú se oculta bajo `lg` y se abre con el botón; sin desplazamiento horizontal.
- **FR-009**: Sin IA, sin interruptores de IA, sin llamadas de red. Ningún dato real ni nombre comercial en plantillas, tests o fixtures: marca «CONFRONTADOR · ERP NOTARIAL», usuarios ficticios, códigos como `EXP-0001`.
- **FR-010**: Las capturas del diseño se leen solo desde fuera del repositorio y no se copian a él.

## Success Criteria *(mandatory)*

- **SC-001**: Las seis pantallas (ingreso, inicio usuario, inicio administrador, expedientes, expediente, resultado) reproducen la disposición y la paleta del diseño según revisión visual del propietario sobre el servidor local.
- **SC-002**: La suite completa pasa; los tests de plantilla cubren: ítem activo y secciones por rol, métricas de Inicio con datos ficticios, chip por estado, paso actual del riel por estado, ausencia de datos sensibles en el contexto de Inicio, y ausencia de la cadena «IA» o «AI» en las plantillas.
- **SC-003**: Cobertura de código nuevo ≥ 80 % y Quality Gate en verde.
- **SC-004**: Ningún archivo nuevo bajo `static/vendor/`; un solo archivo CSS nuevo; ninguna dependencia nueva en `requirements*.in`.
- **SC-005**: `python manage.py check`, `makemigrations --check` y Ruff limpios.

## Assumptions

- El diseño es la referencia visual; cuando el diseño y la función actual difieren (tres zonas de carga frente a dos, botón «Confrontar» por borrador, textos de estado), manda la función actual y se viste con el diseño.
- Iconos del menú: caracteres Unicode o SVG en línea pequeños dentro de la plantilla, como hoy; sin librería de iconos.
- La pantalla «Confrontación» del menú del diseño no existe como módulo aparte: la confrontación vive dentro de cada expediente. Por eso el menú tiene «Inicio» y «Expedientes» (y «Administración» para el administrador).
- Deuda deliberada: fuente empaquetada, filtro por estado en la lista, buscador de módulos, historial de actividad (F6), reportes (F7), tipo de acto (F9).
