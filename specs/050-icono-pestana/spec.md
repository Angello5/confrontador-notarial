# F67 · Icono de la notaría en la pestaña del navegador

**Fecha**: 2026-11-02
**Estado**: implementado; cobertura con datos ficticios.
**Alcance**: `config/settings.py`, `core/context_processors.py`, `templates/core/base.html`, `templates/registration/login.html` y `templates/admin/base_site.html`.

## Origen

La pestaña del navegador mostraba un globo genérico. El usuario pidió el logo de la notaría.

## Comportamiento

- **FR-001**: Con `ERP_ICONO` configurado (URL de la imagen, como `ERP_LOGO`), el ingreso, el ERP y la administración enlazan ese icono. Sin configurar, no hay enlace y el navegador usa su icono por defecto.
- **FR-002**: La imagen no se versiona, igual que el logo: cada notaría la aporta en `static/marca/`. La guía de marca pide usar solo el isotipo por debajo de 140 px de ancho, porque el logo entero no se lee a ese tamaño (`docs/branding/notaria-espinosa.md`).

## Seguridad

Sin cambios de permisos ni de datos personales. La imagen es un archivo estático público, como el logo.

## Verificación

`tests/test_preview_y_marca.py`: el enlace sale en el ingreso y en el ERP, y no sale sin configuración.
