# F40 · Aplicar correcciones con avance y descarga directa

**Fecha**: 2026-10-05  
**Estado**: implementado; servidor cubierto con datos ficticios.  
**Alcance**: `expedientes/views.py`, `templates/expedientes/confrontacion.html`, `templates/expedientes/_modal_aplicando.html`, `static/js/aplicar-correcciones.js` y `static/css/erp.css`.

## Origen

Pedido del usuario (2026-10-05):

- Al aplicar las correcciones, debe aparecer una ventana emergente que anuncie que se están aplicando.
- La ventana lleva una barra de avance del color de la interfaz y sigue su patrón de diseño.
- Cuando la barra termina, el archivo ya está descargado y la ventana solo indica dónde quedó.

Antes, «Aplicar correcciones» llevaba a la página «Documento corregido» y la descarga necesitaba otro clic.

## Comportamiento implementado

- **Ventana de avance**:
  - Al confirmar «Aplicar N correcciones», el modal de confirmación da paso a una ventana con el mismo diseño de los modales de la interfaz.
  - Tiene borde superior verde de éxito, título, barra de avance en azul marino (el trazo de la carga de archivos) y un texto de estado que se anuncia a lectores de pantalla.
- **Fases**:
  - **Aplicando**: el servidor no informa su avance, así que la barra se acerca al 60 % mientras responde.
  - **Descargando**: la barra avanza del 60 al 100 % según los bytes recibidos.
  - **Listo**: el archivo `<borrador>-corregido.docx` ya se descargó. La ventana indica «Se guardó en Descargas/<archivo>» y resume en una línea las cifras de antes: aplicadas, excluidas por usted y no aplicadas. Ofrece «Descargar de nuevo» y «Cerrar».
  - **Error**: el borde pasa al color de peligro y la ventana muestra el mismo mensaje que daba la página («Vuelva a confrontar…»).
- **Cierre**: mientras dura el trabajo, la ventana no se cierra con Esc ni con un clic fuera.
- **Servidor**:
  - Con `Accept: application/json`, `correcciones_aplicar` responde `{archivo, descarga, aplicadas, excluidas, no_aplicadas}`, o `{error}` con estado 400.
  - Sin JavaScript, el formulario se envía como antes y muestra la página «Documento corregido».
  - El nombre del archivo corregido sale de una sola función para la respuesta y para la descarga.

## Límites

- El navegador no informa a la página la carpeta donde guardó el archivo. La ventana indica la carpeta de descargas por defecto («Descargas»).
- Si el usuario configuró otra carpeta, o que el navegador pregunte dónde guardar, el archivo queda donde él elija.
- La primera fase es una estimación: el servidor no informa avance real.

## Verificación

- `tests/test_correccion_expedientes.py`:
  - la respuesta JSON del popup con la descarga y las cifras;
  - el error en JSON (sin confirmar y con una corrida ajena);
  - el resultado incluye el popup, su barra y el script.
- Página de prueba con el CSS, Alpine y el script reales, y un servidor simulado: se recorrieron las fases hasta «Listo» y el caso de error.
