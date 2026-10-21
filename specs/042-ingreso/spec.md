# F54 · Ingreso con la marca más grande y la banda completa

**Fecha**: 2026-10-20  
**Estado**: implementado en la pantalla de ingreso; cobertura con datos ficticios.  
**Alcance**: `templates/registration/login.html` y la sección «Ingreso» de `static/css/erp.css`.

## Origen

El usuario pidió el 2026-10-20: «Login: agrandar el logo y los textos, y completar el lado vacío». La marca y los textos se leían pequeños a la distancia de un escritorio de la notaría. La banda derecha ocupaba media pantalla con una sola frase al pie y, en su lado derecho, el texto blanco caía sobre el verde del degradado.

## Comportamiento implementado

- **Marca más grande**: el logo pasa de 200 a 300 px de ancho (260 px en móvil). Sin logo, el sello pasa de 40 a 60 px (52 px en móvil) y el nombre, de 21 a 30 px (24 px en móvil). El subtítulo «Confrontador Notarial» pasa de 11 a 13 px.
- **Textos y campos más grandes**:

| Elemento | Antes | Ahora |
|---|---|---|
| Título «Ingresar» | 30 px | 40 px (34 px en móvil) |
| Ayuda «Use la cuenta…» | 16 px | 18 px |
| Etiquetas | 14 px | 16 px |
| Campos | 44 px de alto, 15 px | 52 px de alto, 18 px |
| Nota de obligatorios, error y avisos | 13 px | 15 px |
| Botón «Ingresar» | 48 px | 56 px |
| Pie | 13 px | 15 px |

- **Banda derecha completa** (desde 960 px de ancho):
  - un titular: «Revise el proyecto de escritura antes de la firma.»;
  - tres puntos sobre qué hace el sistema, con íconos del sprite existente:
    - confronta el proyecto con la minuta y los recaudos;
    - señala cada observación con su fuente («dice» y «debe decir»);
    - genera el Word con las correcciones que el usuario elige, sin modificar el original;
  - al pie, el nombre y la dirección de la notaría (`ERP_NOMBRE`, `ERP_DIRECCION`). Sin dirección, solo se muestra el nombre.
- **Fondo de la banda**: tinta → marino, con el verde de marca solo como brillo en la esquina superior derecha. Así el texto nunca cae sobre el verde (guía de marca §3.4).
- **Pie de la columna izquierda**: en escritorio se oculta, porque la banda ya muestra el nombre y la dirección. Por debajo de 960 px la banda se oculta y el pie vuelve a mostrarse.
- La caja de ingreso queda centrada en vertical entre la marca y el pie.
- **Error de credenciales**: dice «El nombre de usuario o la clave no son correctos…», con los mismos términos que las etiquetas («Nombre de usuario», «Clave»).

## Requisitos

- **FR-001**: la banda muestra el nombre de la notaría, su dirección si está configurada y los tres puntos sobre el sistema. No usa `aria-hidden`, para que un lector de pantalla también los lea.
- **FR-002**: el ingreso muestra el logo si `ERP_LOGO` está configurado; si no, el sello con las iniciales.
- **FR-003**: el ingreso no carga recursos remotos: todos los `src` y `href` son rutas locales o anclas, y la hoja enlazada lleva `?v={{ static_v }}`.
- **FR-004**: el texto de la banda cumple contraste AA y el foco del teclado se ve con al menos 3:1.
- **FR-005**: la hoja no añade `!important` (regla de Sonar `css:S9423`).

## Seguridad

Sin cambios de permisos ni de autenticación: la vista y el formulario de ingreso no cambian. El nombre, el logo y la dirección llegan del procesador de contexto `core.context_processors.marca` y se escapan como cualquier variable de plantilla. No se escribe ningún dato real de la notaría en el repositorio. Sin dependencias, sin JavaScript y sin recursos remotos.

## UX (principio VIII)

- **Coincidencia con el mundo real (2)**: la banda usa el glosario de F36: proyecto de escritura, minuta, recaudos, observación, «dice» y «debe decir».
- **Consistencia (4)**: los mismos tokens, el sello y el botón verde de la marca. El error usa los mismos términos que las etiquetas.
- **Diseño minimalista (8)**: la banda dice qué hace el sistema en tres líneas; nada de marketing.
- **Accesibilidad**: etiquetas visibles, foco visible y el orden de tabulación de siempre (usuario, clave, botón).
- **Ahorro de tiempo**: el cursor sigue empezando en «Nombre de usuario» (autofoco de Django) y no se añade ningún paso.

## Hallazgos de las skills de diseño

`design:design-critique` sobre las capturas de antes y después:

- Aplicados:
  - la marca (sello de 40 px, nombre de 21 px) y la nota de obligatorios (13 px) eran pequeñas para la distancia de lectura;
  - la banda ocupaba media pantalla con una sola frase y su texto blanco cruzaba el verde del degradado (2,1:1 al final de las líneas; el texto grande exige 3:1);
  - el nombre y la dirección del pie se repetían en escritorio al pasar a la banda, así que el pie se oculta allí;
  - con el pie oculto, `space-between` pegaba la caja al fondo; ahora se centra con márgenes automáticos.
- Descartados:
  - repetir el logo o un sello grande en la banda: la marca ya está arriba a la izquierda, más grande, y la guía prohíbe el logo PNG sobre el degradado;
  - una ilustración SVG: los tres puntos con íconos llenan la banda sin añadir recursos;
  - mostrar la banda en móvil: allí la tarea es solo ingresar y el pie ya da el nombre y la dirección;
  - el eyebrow «Confrontador Notarial» de la banda: repetía el subtítulo de la marca.

`design:ux-copy`:

- El titular y los puntos están escritos con verbos de acción, en presente y tratando al usuario de usted, como el resto del ERP. No prometen más de lo que hace el sistema: el Word lleva las correcciones que el usuario elige, porque no toda observación tiene corrección automática (F48).
- El error decía «contraseña», pero la etiqueta dice «Clave»; ahora usa «nombre de usuario» y «clave».
- Se conservan «Ingresar» como título y botón, la ayuda «Use la cuenta que le asignó la notaría.» y la nota de obligatorios, que es el patrón de los demás formularios.

`design:accessibility-review` (WCAG 2.1 AA) sobre el resultado:

- **Contraste**, medido en las capturas sobre el fondo más claro junto a cada texto:
  - titular blanco: 9,3:1;
  - puntos: 14:1;
  - nombre y dirección (`#DFE4F2`): 11:1;
  - ícono verde sobre su recuadro: 7:1;
  - ayuda `#4B5D8C` sobre blanco: 6,5:1;
  - botón tinta sobre verde: 10,2:1.
- **Corregido durante la revisión**: el foco global del ERP (`#44D880` sobre blanco) da 1,85:1. En el ingreso se usa el verde AA `#01835D` (4,8:1), como en el admin desde F49.
- **Teclado**: el orden es usuario → clave → botón, con el contorno visible en cada uno. Comprobado con Brave headless por CDP.
- **Landmarks**: `main` con el título «Ingresar» y `aside` etiquetado por su titular (`h2`). Los íconos y el sello son decorativos (`aria-hidden`) y el logo lleva el nombre como `alt`.
- **Movimiento**: la pantalla no tiene animaciones. Con `prefers-reduced-motion: reduce` la transición del botón queda en 0 s (regla global existente).
- **Reflujo y tamaños**: a 320 px no hay desplazamiento horizontal. A 390 px los campos miden 52 px y el botón 56 px, por encima de 44 px.

## Capturas

Fuera del repositorio, con datos ficticios: 1280 y 390 px, antes y después, con sello y con un logo ficticio, foco y error.

## Pendiente de confirmar

- Si el foco verde AA (`#01835D`) debe extenderse a todo el ERP. Hoy solo cambia en el ingreso y en el admin.
