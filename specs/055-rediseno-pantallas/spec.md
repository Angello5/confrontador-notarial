# F73 · Rediseño de Inicio, kardex, resultado e informe

**Fecha**: 2026-11-03
**Estado**: implementado; cobertura con datos ficticios.
**Alcance**: `templates/core/home.html`, `core/views.py`, `expedientes/services.py`, `static/js/inicio-admin.js`, `templates/expedientes/detalle.html`, `_zona_continua.html`, `core/_riel.html`, `static/js/carga-expediente.js`, `templates/expedientes/confrontacion.html`, `_vista_borrador.html`, `_obs_detalle.html`, `_reporte_contenido.html` y `static/css/erp.css`.

## Origen

El usuario revisó en Claude Design cuatro propuestas con dos opciones cada una y eligió: **1a** barra de filtros (Inicio), **2b** siguiente paso (kardex), **3a** modal amplio (vista previa del informe) y **4a** detalle en la lista (resultado).

## Comportamiento

### Inicio del administrador (1a)

- **FR-001**: Una barra permite filtrar por periodo (Hoy, Ayer, Esta semana, Este mes, Rango de fechas) y por persona. Muestra qué filtros están activos, cada uno con su botón para quitarlo, y «Limpiar filtros». Sin filtros se conserva el periodo predeterminado.
- **FR-002**: `/inicio/datos/` acepta `filtro`, `desde`, `hasta` y `usuario`. Un valor no válido se ignora y la respuesta indica qué filtro se aplicó de verdad. Las fechas se calculan en el servidor, en hora local.
- **FR-003**: El periodo acota la calidad de la confrontación y las últimas confrontaciones. La actividad conserva «Por semana / Por mes» y resalta las barras dentro del periodo. Los totales de kardex y transferencias no dependen de ningún filtro.
- **FR-004**: La persona es quien creó el kardex, el mismo criterio del ranking (F57), y acota actividad, calidad y últimas confrontaciones. La lista ofrece a quienes tienen kardex confrontados en cualquier fecha, para que elegir un periodo no borre la persona elegida.
- **FR-005**: El informe impreso del Inicio indica periodo y persona.

### Kardex (2b)

- **FR-006**: Cada grupo (minuta, recaudos, borrador) es una sección propia con su resumen. A la derecha, fija, va una columna con las etapas, «¿Qué debe hacer?», el botón de confrontar y por qué está deshabilitado.
- **FR-007**: Cada archivo dice su estado y su nota: en cola, leyendo desde qué hora, texto extraído o que no se pudo leer.
- **FR-008**: «Volver a subir», en un documento que no se pudo leer, abre el selector de archivos y solo elimina el documento si se eligió un archivo admisible. Si se cancela, no cambia nada. Encadena las dos acciones que ya existían.

### Resultado (4a)

- **FR-009**: Un solo encabezado compacto reúne el kardex, el resumen, los filtros de severidad y las acciones.
- **FR-010**: Al elegir una observación se despliega en la lista su detalle: motivo, fuente, si no se ubicó en las páginas, la casilla de corrección o por qué no la admite, y su posición con anterior y siguiente. Lo hallado y lo correcto siguen en la fila (F65), sin repetirse en el detalle.
- **FR-011**: El visor muestra la observación elegida y la leyenda dice el trazo de cada severidad.
- **FR-012**: En pantallas estrechas, dos pestañas separan «Borrador» y «Observaciones». Desde el detalle se puede saltar al borrador.

### Vista previa del informe (3a)

- **FR-013**: «Vista previa del informe» abre un modal amplio con el contenido a la izquierda y el informe a la derecha. Marcar o desmarcar una sección actualiza la vista al instante, y son las mismas casillas de «Descargar informe».
- **FR-014**: La vista previa copia el informe imprimible ya renderizado; no pide datos nuevos. Avisa que el diseño y la paginación pueden variar en Word. Si no hay secciones marcadas, lo dice y deshabilita la descarga. Si falla, ofrece reintentar.

## Decisiones

- **«Ilegible» y «error» siguen siendo un mismo estado**: distinguirlos exige un campo de motivo que la propuesta dejó fuera.
- **«Por mes» conserva lo que va del año (F53)**: la nota de la propuesta dice que la función actual no cambia, aunque su maqueta rotula «12 meses».
- **Atribución**: la fase del flujo entre dos personas (reservada como F72) puede cambiar FR-004.

## Seguridad

`/inicio/datos/` sigue siendo exclusivo del administrador; la lista de personas solo llega ahí, con nombre e identificador. «Volver a subir» usa las mismas rutas, permisos y validaciones que eliminar y adjuntar. La vista previa no expone datos que la página no tuviera ya.

## Requisitos de UX (principio VIII)

Estado visible (filtros activos, «¿Qué debe hacer?»), control del usuario (quitar filtros, cancelar «Volver a subir»), reconocimiento (etapas, leyenda con el trazo) y minimalismo (encabezado único, detalle solo de la observación elegida). Severidad y etapas no dependen solo del color.

## Verificación

- `tests/test_inicio.py`, `tests/inicio_frontend.test.cjs`: filtros, valores no válidos, permisos y parámetros.
- `tests/test_expedientes_ui.py`, `tests/carga_frontend.test.cjs`: columna de estado, motivo del botón y «Volver a subir».
- `tests/test_expedientes_confrontacion_ui.py`: encabezado, detalle en la lista, pestañas y vista previa.
