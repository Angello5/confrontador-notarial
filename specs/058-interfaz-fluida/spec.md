# F77 · Interfaz fluida

**Fecha**: 2026-11-16
**Estado**: implementado; revisado en la pantalla de ingreso. Las pantallas internas quedan por revisar con una sesión iniciada.
**Alcance**: `static/css/erp.css`, `static/js/carga-expediente.js`, cinco plantillas y `tests/carga_frontend.test.cjs`. Solo presentación: no cambia reglas, datos, rutas ni permisos.

## Origen

El usuario pidió que la interfaz se sienta más fluida. La interfaz ya tenía movimiento en algunos puntos (desplegables, panel nuevo, ranking), pero faltaba en los que más se notan:

- al pasar de una página a otra la pantalla parpadeaba en blanco;
- los botones no respondían a la pulsación;
- las ventanas y los avisos aparecían con un movimiento mínimo y desaparecían de golpe;
- un documento en lectura solo cambiaba el texto de su etiqueta;
- mientras se preparaba la vista del borrador quedaba un hueco.

## Criterio

Cada movimiento tiene un propósito y se decide por la frecuencia con que se ve:

| Elemento | Frecuencia | Decisión |
|---|---|---|
| Pulsar un botón | Constante | 120 ms, solo escala a 0,97 |
| Cambiar de página | Decenas al día | Fundido de 90 ms al salir y 220 ms al entrar; el menú y la barra quedan quietos |
| Ventanas y avisos | Ocasional | 160 a 220 ms, entrada desde abajo, salida con fundido |
| Documento en lectura | Ocasional, dura minutos | Línea que avanza y borde de color |
| Documento que termina | Ocasional | Un destello verde, una sola vez |
| Estado vacío e ingreso | Raro | Entrada de 300 a 350 ms |
| Listas y tablas al cargar | Decenas al día | Sin entrada escalonada: retrasaría el trabajo |

Guía de marca (`docs/branding/notaria-espinosa.md`, §Movimiento): 150 a 250 ms, salida suave, sin rebotes.

## Comportamiento

- **FR-001**: Los botones ceden al pulsarlos (escala 0,97 en 120 ms). No aplica a los deshabilitados ni a los que son un enlace de texto.
- **FR-002**: Al navegar entre páginas del ERP, el contenido se funde en lugar de parpadear; el menú lateral y la barra superior no se animan. Es una mejora progresiva (`@view-transition`): el navegador que no la admite navega como antes.
- **FR-003**: Las ventanas entran con el fondo en fundido y la ventana creciendo desde 0,97; al cerrarse, se funden en 160 ms.
- **FR-004**: Los avisos flotantes entran desde abajo y salen con un fundido corto.
- **FR-005**: La etiqueta de estado de un documento cambia de color sin salto. Mientras se lee, su fila muestra una línea que avanza y el icono gira.
- **FR-006**: El documento que termina de leerse durante la visita se confirma con un destello verde, una sola vez. Los que ya estaban listos al abrir la página no destellan.
- **FR-007**: Mientras se prepara la vista del borrador se muestra una hoja en espera, además del texto que ya existía.
- **FR-008**: Con «reducir movimiento» activado en el sistema, no hay animaciones ni transición entre páginas.
- **FR-009**: Solo se animan la opacidad y la transformación, salvo los cambios de color y el brillo de la hoja en espera. Sin bibliotecas ni archivos nuevos.

## Fuera de alcance

- **Imágenes o animaciones generadas** (Higgsfield u otra herramienta). Las mejoras de fluidez se resuelven con CSS. Una ilustración para los estados vacíos sí podría aportar, y la guía de marca la admite (vector plano); queda como decisión del usuario, porque añade archivos de imagen al repositorio.
- Entrada escalonada de filas en listas y tablas.
- Cambiar la disposición, los colores o los textos de las pantallas.
- Bandeja de documentos con estados por etapa: fase posterior.

## Seguridad

Sin cambios de permisos ni de datos. Sin recursos externos: no se cargan fuentes, imágenes ni scripts de otros dominios.

## UX (principio VIII)

- **Visibilidad del estado (1)**: la lectura en curso y su final se ven sin leer la etiqueta.
- **Consistencia (4)**: una sola curva y tres duraciones (`--ne-salida`, `--ne-t-pulso`, `--ne-t-corta`, `--ne-t-media`) para todo el ERP.
- **Estética minimalista (8)**: nada se anima por adorno en lo que se usa a diario.
- **Accesibilidad**: se respeta «reducir movimiento»; el foco visible no cambia; la hoja en espera es decorativa (`aria-hidden`) y el aviso de texto conserva su `role="status"`.

## Verificación

- `tests/carga_frontend.test.cjs`: solo el documento que termina en esta visita queda como recién listo, se conserva entre sondeos y se pierde si pasa a error.
- En el navegador, pantalla de ingreso: la hoja de estilos carga sin errores, con la regla de transición entre páginas y las animaciones nuevas.
- Pendiente con una sesión iniciada: navegación entre páginas, ventanas, avisos, lectura de un documento y vista del borrador.
