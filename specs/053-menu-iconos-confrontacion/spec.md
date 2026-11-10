# F70 · Menú de iconos en la confrontación

**Fecha**: 2026-11-02
**Estado**: implementado; cobertura con datos ficticios.
**Alcance**: `templates/core/base.html`, `templates/expedientes/confrontacion.html` y `static/css/erp.css`.

## Origen

El usuario pidió que, en la pantalla de confrontación, el panel izquierdo se achique y muestre solo iconos, para tener más espacio para ver el documento.

## Comportamiento

- **FR-001**: En la pantalla de confrontación, en pantallas de 960 px o más, el menú lateral es una franja de 72 px: el icono de la notaría (F67), los iconos del menú y el avatar.
- **FR-002**: Al pasar el puntero o entrar con el teclado, el menú se abre completo sobre el contenido, sin mover el documento. Al salir vuelve a la franja.
- **FR-003**: Sin `ERP_ICONO`, o si la imagen no carga, se muestra el sello con las iniciales.
- **FR-004**: Las demás pantallas, el móvil (menú que se abre con el botón) y el informe impreso no cambian.

## UX (principio VIII)

- Los nombres de los enlaces siguen disponibles para lectores de pantalla con el menú reducido.
- Teclado: al enfocar un enlace del menú, este se abre y se ven sus nombres.

## Seguridad

Sin cambios de permisos ni de datos.

## Verificación

`tests/test_correccion_expedientes.py`: la clase del menú reducido sale en la confrontación y no en la lista de kardex. El aspecto se revisó en el navegador con datos ficticios.
