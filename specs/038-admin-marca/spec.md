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
- **Texto** marino en lugar de negro, texto secundario pizarra (`#4B5D8C`), fondos de banda lavanda (`#EDEFF8`) y estados con los colores de la guía de marca (§8).
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

- La columna «Failed login attempts» del listado sigue en inglés: es el `verbose_name` del campo y cambiarlo exige una migración.
