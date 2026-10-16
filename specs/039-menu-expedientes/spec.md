# F47 · Menú lateral «Expedientes» con submenú

**Fecha**: 2026-10-16  
**Estado**: implementado en la barra lateral; cobertura con datos ficticios.  
**Alcance**: `templates/core/base.html` y la regla del menú en `static/css/erp.css`.

## Origen

El usuario pidió el 2026-10-16: «En la parte lateral izquierda en el menu kardex quiero que sea un submenu. Expedientes -Kardex y -Transferencia vehicular».

## Comportamiento implementado

- La entrada «Kardex» del menú lateral pasa a ser el grupo **«Expedientes»**, con el mismo ícono. Debajo cuelgan, con el estilo de submenú de F44 (sangría, guía vertical y letra menor):
  - «Kardex», que lleva a la lista de kardex (`expediente_lista`);
  - «Transferencia vehicular», que lleva a su lista (`vehicular_lista`).
- «Expedientes» solo rotula el grupo: no es un enlace ni un destino propio. El submenú está siempre visible y no usa JavaScript.
- Accesibilidad: el submenú es una lista con `aria-label="Expedientes"`. Solo los dos hijos reciben foco con el teclado. La entrada activa se marca con `aria-current="page"` con la misma regla de antes:
  - «Kardex» en las rutas de `expedientes/` que no son de transferencia vehicular;
  - «Transferencia vehicular» en su lista y en los kardex de tipo vehicular.
- **Matiz a F36**: F36 cambió «Expedientes» por «Kardex» en toda la interfaz. F47 recupera «Expedientes» solo como rótulo del grupo en la barra lateral. Las migas de pan, los títulos, los mensajes y las URL no cambian.

## Requisitos de seguridad

Sin cambios. El grupo se muestra con las mismas condiciones que la entrada anterior (rol Administrador o Usuario), y cada vista mantiene sus permisos.

## Verificación

- `tests/test_vehicular_ui.py::test_menu_expedientes_agrupa_kardex_y_transferencia_vehicular` reemplaza la prueba de F44 que colgaba «Transferencia vehicular» de «Kardex». Comprueba:
  - que el grupo no es un enlace;
  - el `aria-label` del submenú;
  - el orden de los dos hijos;
  - el `aria-current` en la lista vehicular.
- `tests/test_shell.py` sigue comprobando que «Kardex» queda activo en la lista y en el detalle.

## Seguimiento · versión de los estáticos (2026-10-16)

Tras mergear F47, el navegador siguió usando el `erp.css` anterior y «Expedientes» se vio sin estilo: Django sirve los estáticos solo con `Last-Modified` y el navegador los reutiliza durante horas. Desde ahora cada enlace a un CSS o JS propio lleva `?v=` con una huella corta del contenido de `static/` (`core.context_processors.version_estaticos`, expuesta como `static_v`). Se calcula al arrancar el servidor, así que basta reiniciarlo tras actualizar. En el despliegue (F8) puede sustituirse por `ManifestStaticFilesStorage`. Pruebas en `tests/test_version_estaticos.py`.
