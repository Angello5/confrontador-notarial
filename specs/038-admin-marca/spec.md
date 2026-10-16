# F46 · Interfaz de administración con la marca de la notaría

**Fecha**: 2026-10-16  
**Estado**: implementado en el Django admin (`/admin/`), incluido su ingreso; cobertura con datos ficticios.  
**Alcance**: `templates/admin/base_site.html`, `static/css/admin.css`, `accounts/admin_site.py` y `accounts/apps.py`.

## Origen

El usuario pidió el 2026-10-16 cambiar el aspecto visual de la interfaz de administración tomando como referencia la marca actual. El Django admin, donde se gestionan las cuentas (principio VI), conservaba los colores por defecto de Django, ajenos al resto del ERP.

## Principio

Se reutiliza lo que ya existe: la marca de `docs/branding/tokens.css` aplicada al ERP en F29 y el fragmento `core/_marca.html` con el nombre y el logo configurables desde F28. El admin solo cambia de piel: sin paquetes de temas, sin dependencias nuevas, sin fuentes ni recursos remotos y sin tocar `static/css/erp.css` ni `templates/core/base.html`.

## Comportamiento implementado

- **Cabecera** blanca con la marca de la notaría (logo si `ERP_LOGO` está configurado; si no, el sello con las iniciales y el nombre de `ERP_NOMBRE`), el rótulo «Administración» y una línea verde inferior. Es blanca también en modo oscuro, porque el logo no tiene versión en negativo.
- **Migas de pan, títulos de módulo y filtros** sobre marino (`#0F2765`); la aplicación activa del menú lateral en verde.
- **Botones**: marino con texto blanco; el principal («Guardar») en verde con texto tinta (`#00112C`), como el CTA de la marca. Esquinas de 2 px: la marca es rectilínea.
- **Texto** marino en lugar de negro, texto secundario pizarra (`#4B5D8C`), fondos de banda lavanda (`#EDEFF8`; desde F49, blancos) y estados con los colores de la guía de marca (§8).
- **Modo oscuro** del admin (automático o elegido con su botón): fondo tinta (`#00112C`), superficies marino y enlaces en verde.
- **Título de la pestaña**: «<página> | Administración · <nombre de la notaría>».
- **Ingreso** (`/admin/login/`): misma cabecera; la caja se ensancha para que la marca quepa en una línea y en móvil se acomoda en dos.
- La aplicación de cuentas se muestra como «Cuentas» (antes «Accounts») en el menú, el índice y las migas de pan.
- Tipografía: Nunito Sans y Prompt si están instaladas en el equipo; si no, las del sistema (igual que el ERP).

## Requisitos

- **FR-001**: todas las páginas del admin, incluido el ingreso, muestran el nombre configurado de la notaría y cargan `static/css/admin.css`.
- **FR-002**: la hoja no carga recursos remotos (`://`, `@import`).
- **FR-003**: la hoja redefine los colores del modo claro y del oscuro con los mismos selectores que Django (`:root`, `html[data-theme="light"]`, `html[data-theme="dark"]` y `prefers-color-scheme: dark`).
- **FR-004**: texto y controles cumplen contraste WCAG AA en ambos modos; el blanco nunca va sobre el verde de marca.

## Seguridad

Sin cambios de permisos: el admin sigue restringido al rol Administrador (principio VI). El nombre y el logo llegan del procesador de contexto existente y se escapan como cualquier variable de plantilla. No se tocan datos personales.

## UX (principio VIII)

- Consistencia (4): la misma paleta, sello y tipografía que el ERP.
- Coincidencia con el mundo real (2): «Cuentas» en lugar de «Accounts».
- Accesibilidad: contraste AA y el foco por defecto de Django se conserva.

## Fuera de alcance

- ~~La columna «Failed login attempts» del listado sigue en inglés~~: resuelto en F49 sin migración («Intentos fallidos»).

## F49 · Fondo blanco y panel más interactivo (2026-10-16)

El usuario aprobó la marca de F46 y pidió el 2026-10-16 que el fondo también sea blanco y que el panel sea más interactivo, usando las skills de UI/UX. Alcance: `static/css/admin.css`, `accounts/admin_site.py`, `accounts/admin.py`, `templates/admin/index.html` (nuevo) y `templates/admin/accounts/user/action_confirmation.html`. Sin JavaScript, sin dependencias y sin recursos remotos.

### Comportamiento implementado

- **Fondo blanco** en el modo claro, también en el ingreso. Las superficies que eran lavanda (barra de búsqueda, filtro, filas alternas, barra de botones, «Acciones recientes») pasan a blanco con bordes finos. El tinte claro (`#F6F7FC`) queda solo para estados: hover y columna ordenada. El modo oscuro no cambia de paleta.
- **Índice con resumen de cuentas**: tres recuadros (Todas, Activas, Inactivas) con el recuento y una línea de apoyo, sobre la lista de aplicaciones. Cada recuadro abre la lista de usuarios ya filtrada por estado (`?is_active__exact=1|0`). Reutiliza `core/_metrica.html`, la métrica del inicio del ERP. Tienen hover y foco, y una flecha que se desplaza (se oculta en móvil).
- **Sin menú lateral** (`enable_nav_sidebar = False`): hay un solo modelo y las migas de pan bastan. El contenido gana unos 300 px.
- **Listado**: hover en las filas. La fila seleccionada (fondo verde claro, ya de Django) se marca con una franja verde. Con algo seleccionado, la barra de acciones se resalta, el contador pasa a negrita y «Ir» se vuelve botón principal (CSS `:has()`, sin JS). «Añadir usuario» va en marino, como botón principal de la página.
- **Columna «Intentos fallidos»** en lugar de «Failed login attempts». Es un método de `UserAdmin` ordenable por el campo, así que no hace falta migración (resuelve el «Fuera de alcance» de F46).
- **Jerarquía de botones**: Guardar en verde; «Guardar y añadir otro» y «Guardar y continuar editando» con borde (secundarios); acción destructiva en rojo.
- **Confirmación de desactivar/reactivar**: antes era un botón nativo sin estilo. Ahora usa la barra de botones del admin, con el verbo y el recuento («Desactivar 1 cuenta», en rojo, o «Reactivar 2 cuentas») y «Volver sin cambios».
- **Ingreso**: página blanca, caja con borde y botón «Iniciar sesión» verde a todo el ancho, igual que el CTA de la marca.
- **Mensajes**: franja izquierda del color del estado, además del icono de Django.
- **Foco visible de marca** en enlaces, campos y botones: contorno de 3 px verde `#01835D` sobre blanco y `#44D880` en modo oscuro, sobre marino (migas y cabeceras de módulo) y en las casillas (`accent-color`).
- **Movimiento**: transiciones de 150 ms solo con `prefers-reduced-motion: no-preference`. Con `reduce` se anulan también las de Django.

### Requisitos

- **FR-005**: en modo claro, el fondo de las páginas del admin, incluido el ingreso, es blanco (`--darkened-bg: #fff`).
- **FR-006**: el índice muestra el total de cuentas, las activas y las inactivas, con enlaces a la lista filtrada.
- **FR-007**: el foco del teclado es visible en todo control (`:focus-visible`) con contraste ≥ 3:1 frente al fondo.
- **FR-008**: las transiciones se desactivan con `prefers-reduced-motion: reduce`.
- **FR-009**: la hoja no usa `!important` (regla de Sonar `css:S9423`).

### Hallazgos de las skills de diseño

`design:design-critique` sobre las capturas previas:

- Aplicados: las bandas lavanda competían con la cabecera blanca aprobada; el índice era una tabla de una fila sin visión del estado; el menú lateral con un solo modelo ocupaba 300 px y duplicaba las migas; Guardar y los dos secundarios tenían el mismo peso; la confirmación tenía un botón nativo sin estilo y un verbo genérico; el foco de los campos era casi invisible (solo cambiaba el borde); el botón de ingreso iba en marino y el de Guardar en verde; había una columna en inglés.
- Descartados:
  - cabecera de tabla fija: como mucho hay 10 usuarios (constitución), así que la tabla nunca es larga;
  - iconos en los mensajes: Django ya los muestra;
  - JavaScript propio: `:has()` y el `actions.js` de Django cubren la selección y el contador;
  - cambiar el título «Seleccione usuario a modificar»: es el estándar de Django y no bloquea;
  - un recuadro de cuentas bloqueadas: no hay filtro al que enlazar y exigiría uno nuevo.

`design:ux-copy`:
- Recuadros: «Todas» / «Activas» / «Inactivas», con «Registradas en el sistema», «Con acceso al ERP» y «Sin acceso al ERP». Se evitó repetir «Cuentas», que ya titula el módulo.
- Botones de confirmación con el verbo y el recuento, y «Volver sin cambios» en lugar de «Cancelar».
- Columna «Intentos fallidos».

`design:accessibility-review` (WCAG 2.1 AA) sobre el resultado:

- **Contraste**: todo lo nuevo pasa. Secundarios `#0F2765`/blanco 14:1, peligro blanco/`#C8283C` 5,5:1, etiquetas de métrica `#4B5D8C`/blanco 6,5:1, contador en la barra seleccionada 12,8:1, foco `#01835D`/blanco 4,8:1 y `#44D880`/`#00112C` 10,2:1.
- **Corregido durante la revisión**: el foco verde AA sobre las bandas marino daba 2,9:1. Ahí se usa el verde vivo (7,6:1).
- **Corregido durante la revisión**: la flecha decorativa de los recuadros se leía en voz alta. Ahora usa `content: "→" / ""`.
- **Teclado**: el orden de tabulación es lógico (saltar al contenido, marca, herramientas, recuadros, módulo) y todos los controles muestran el contorno. Comprobado con Brave headless.
- **Movimiento**: con `reduce` todas las transiciones quedan en 0 s. Comprobado por CDP.
- **Tamaños táctiles**: los recuadros y botones superan los 35 px. Los enlaces de la barra de usuario de Django son pequeños, pero 2.5.5 es nivel AAA y no se tocan.

### UX (principio VIII)

- Visibilidad del estado (1): recuentos en el índice y feedback de selección.
- Prevención de errores (5): el botón destructivo es rojo y dice qué hará y a cuántas cuentas.
- Consistencia (4): la métrica del inicio del ERP y el CTA verde también en el ingreso.
