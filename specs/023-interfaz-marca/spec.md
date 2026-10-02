# Feature Specification: F29 · Interfaz con la marca de la notaría

**Created**: 2026-10-02

**Status**: Plantillas, CSS, marca del backend y revisión de correcciones verificados localmente el 2026-10-02. Véase `docs/auditoria-2026-10-02.md` para evidencia y límites.

**Input**: Handoff de diseño «Confrontador Notarial» (Claude Design) y acuerdos de la reunión de construcción del 2026-09-28: logo de cada notaría, carga de varios archivos con su estado, lista de errores imprimible o descargable en Excel/PDF.

## Principio

**Toda la apariencia vive en `static/css/erp.css` y en las plantillas; el backend no cambia de contrato.** Las plantillas usan las mismas variables de contexto, URLs y formularios que F14–F28. Las funciones nuevas se resuelven en el navegador (Alpine) con los datos ya renderizados.

## Qué cambió

- **Shell**: barra lateral blanca con logo o sello, migas, «Sesión segura · rol», avisos (`messages`) como toasts. AdminLTE ya no se carga (el archivo sigue en `static/vendor/`).
- **Íconos**: sprite SVG inline (`core/_iconos.html`, trazos Lucide, ISC). Sin CDN.
- **Ingreso**: dos columnas con banda en degradado; campos renderizados sin crispy.
- **Inicio**: métricas que abren la lista filtrada (`?estado=`), «Requieren su atención», últimos expedientes, acceso rápido por rol.
- **Lista**: búsqueda por código, filtro por estado con conteos, orden por fecha, menú por fila (Editar / Eliminar con modal), `?nuevo=1` abre el formulario.
- **Detalle**: chip de estado, riel de 4 pasos con estado (Completado, En curso, Pendiente, Con error), carga por arrastre que se envía sola, eliminar con modal.
- **Resultado**: resumen y filtro por severidad, pestañas por capa, lista + detalle con fragmento del borrador resaltado, navegación con ↑/↓, corrección marcable desde cada observación, barra fija «Aplicar correcciones» con modal de confirmación (mismo POST de F15), **reporte**: «Word» por defecto (`static/js/reporte-docx.js`: .docx ejecutivo generado en el navegador, sin dependencias, con logo en el encabezado, ficha, resumen ejecutivo con indicadores por severidad, prioridades, tablas por capa con encabezado repetido y «Página X de Y»), «Imprimir o guardar PDF» (sección imprimible) o «Excel» (CSV con BOM y `;`, protegido contra fórmulas).
- **Historial / Corrida**: tabla con severidades; botón para imprimir o guardar la corrida en PDF.

## Configuración y mejoras opcionales

- **FR-001 (logo)**: el context processor de F28 expone también `erp_logo` (URL, variable de entorno `ERP_LOGO`, vacía por defecto). Sin valor se muestra el sello con `erp_iniciales`. Cambio en el backend:

  ```python
  # config/settings.py, junto a ERP_NOMBRE
  ERP_LOGO = os.environ.get("ERP_LOGO", "").strip()

  # core/context_processors.py, en el diccionario que devuelve marca()
  "erp_logo": settings.ERP_LOGO,
  ```

  Notaría Espinosa: el logo oficial (PNG 800×181, de notariaespinosa.com) está en `static/marca/logo.png`, fuera del control de versiones; en su entorno, `ERP_LOGO=/static/marca/logo.png`.
- **FR-002 (dirección)**: opcional, `erp_direccion` (variable `ERP_DIRECCION`) para el pie del ingreso.
- **FR-003 (fuentes)**: vendorizar Prompt y Nunito Sans (OFL) en `static/vendor/fonts/` con `@font-face`; hoy se usan si están instaladas y, si no, la fuente del sistema.
- **FR-004 (reporte)**: el reporte no muestra la versión del catálogo porque `confrontacion.html` no la recibe; añadir `resultado.version_catalogo` y la fecha/usuario de la corrida si se quieren en el encabezado.

## Tests que deben actualizarse

Cambian por decisión de diseño (verificado renderizando las plantillas con datos ficticios):

- `test_expedientes_ui`: `">Actualizado</th>"`. Ahora el encabezado es un botón de orden.
- `test_expedientes_confrontacion_ui`:
  - `"<h1>Resultado de la confrontación</h1>"`. Ahora el h1 es el código y «Resultado de la confrontación» es la ceja.
  - `'<details class="card mb-3"'`. Ahora es `class="panel desplegable"`.
  - `'class="chip" data-estado="REVISION">2</span>'`. Los conteos están en las pestañas (`capa-num`).

El resto de las aserciones de `test_shell`, `test_codigo_y_marca`, `test_expedientes_ui` y `test_expedientes_confrontacion_ui` se mantiene.

## Assumptions

- La corrección propuesta se liga a una observación solo cuando coincide de forma única el par valor hallado/valor esperado, normalizando espacios y mayúsculas. No se enlazan subcadenas de un número mayor. Las que no se emparejan siguen en el modal «Aplicar correcciones».
- Excel se entrega como CSV (abre en Excel sin dependencias nuevas). [NEEDS CLARIFICATION] ¿Se requiere `.xlsx` nativo? Haría falta `openpyxl` y una vista de descarga.

## Verificación del 2026-10-02

- FR-001 y FR-002 implementados y cubiertos por pruebas de contexto. Las fuentes del sistema siguen siendo el fallback disponible; FR-003 y FR-004 son mejoras pendientes de presentación, sin bloquear la confrontación.
- El fragmento se centra en el valor observado y conserva índices del texto original para resaltar acentos y espacios correctamente. La vista permite aceptar o excluir sustituciones propuestas; la edición libre del documento completo se realiza sobre el Word descargado.
- Las nuevas corridas guardan sus propuestas de corrección. Al reabrirlas se conserva el identificador de corrida y se comprueba la existencia del original antes de habilitar la corrección. Las corridas antiguas sin propuestas guardadas requieren volver a confrontar.
- Los errores al generar Word liberan el botón y muestran un mensaje recuperable. Los controles de carga tienen identificadores únicos por rol.
- Los tests de interfaz se actualizaron al diseño aprobado conservando sus comprobaciones funcionales. La navegación, la reapertura del resultado, el reporte y la aplicación de correcciones se comprobaron con datos ficticios en el navegador.
