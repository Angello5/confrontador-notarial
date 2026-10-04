# Research: F32 · Vista del borrador con errores resaltados

## R1. Cómo convertir un `.docx` en páginas

- **Decision**: convertir el original conservado a PDF con LibreOffice headless reutilizando
  `adaptadores.extraccion._soffice` (añadiendo `.docx` a los sufijos admitidos), y dibujar cada
  página con PyMuPDF (`page.get_pixmap`).
- **Rationale**: ambas herramientas ya están fijadas y aprovisionadas (F3, F31), funcionan sin
  internet, y LibreOffice ya convierte los `.doc`. El PDF da también la posición de cada palabra
  (R3).
- **Alternatives considered**: renderizar el `.docx` a HTML en el navegador (docx-preview o
  mammoth): es una dependencia nueva y no reproduce la paginación. Usar Word por COM en Windows: no
  es portable y depende de la decisión de despliegue de F8.

## R2. Dónde vive el PDF de vista

- **Decision**: guardarlo como caché en `EXPEDIENTES_TEMP_DIR` con el nombre
  `vista-<expediente>-<documento>-<sha256[:16]>.pdf`, escrito en un temporal y renombrado de forma
  atómica.
- **Rationale**: es un derivado del original y no un archivo documental. `limpiar_temporales` ya
  borra los huérfanos de más de 24 h (no lo referencia ningún `Documento.ruta_temporal`). El
  directorio temporal no se respalda (principio IV). Si la caché se borró, se regenera.
- **Supresión**: `eliminar_documento` y `suprimir_texto_expediente` borran también
  `vista-<expediente>-*`.
- **Alternatives considered**: junto al original en `EXPEDIENTES_ORIGINALES_DIR`: la 1.7.0 solo
  autoriza conservar el original y los corregidos. Convertir en cada petición: unos 3 a 10 s por
  página, lo que incumple SC-003.

## R3. Cómo ubicar el valor sobre la página

- **Decision**: una función pura `nucleo.correccion.marcas(segmentos, valor)`, junto a `coincidencias`.
  - Cada segmento es `(texto, x0, y0, x1, y1, linea)` en fracciones del tamaño de la página.
  - La función reconstruye el texto de la página: une los segmentos de una línea con espacio y
    separa las líneas con `\n`, y registra el desplazamiento de cada segmento.
  - Busca con `correccion.coincidencias(texto, valor)`, la misma normalización de mayúsculas,
    tildes, espacios y límites de palabra que usan la ubicación y la corrección actuales.
  - Para cada coincidencia devuelve un rectángulo por segmento tocado. Dentro de un segmento, los
    bordes se estiman por la proporción de caracteres.
  - Devuelve todas las apariciones, en orden de lectura.
- **Segmentos de un PDF con texto** (incluido el que sale del `.docx`):
  `page.get_text("words")`, agrupados por `(bloque, línea)`. Cada palabra es un segmento, así que
  la proporción solo se usa si el valor es parte de una palabra.
- **Segmentos de una página OCR (Tramo B)**: las `cajas` guardadas en `TextoExtraido.calidad`
  (F31), ya con su texto. Se ordenan en filas con la misma lógica de `calidad_ocr.resumir`
  (inclinación y `tol`). Esa lógica se extrae a `ordenar_filas()` para que el texto reconstruido
  sea idéntico al que confrontó el núcleo. Las coordenadas están en píxeles de la imagen analizada
  (`DPI` = 200 o la imagen original) y se pasan a fracciones con `dimensiones`. Si hubo `giro`, la
  página se muestra con ese mismo giro.
- **Rationale**: el valor está en el texto del borrador porque el núcleo lo encontró ahí. Al buscar
  con la misma función, la ubicación es coherente con la confrontación y determinista.
- **Alternatives considered**: `page.search_for` de PyMuPDF: no comparte la normalización del
  núcleo (tildes, Ñ, límites de palabra). Mapear la línea del texto extraído a la línea del PDF: el
  `.docx` se extrae del XML y su numeración de líneas no coincide con la paginación.

## R4. Qué valor y qué observaciones

- **Decision**: se usa el mismo valor que hoy resalta el fragmento (`data-marcar`): `hallado` en
  identidad y regla, y `palabra` en lingüístico. Una observación con `ubicacion.linea = None`
  cuenta como "No ubicada" sin buscarse en la página, porque el núcleo ya determinó que el valor no
  está en el borrador (ausencias). Si tiene línea pero no se encuentra en las páginas (por ejemplo,
  un guion de corte), también cuenta como no ubicada, con el motivo "no se encontró en la página
  dibujada".
- **Identificadores**: los mismos de la plantilla, `p<n>`, `r<n>` y `o<n>` (`forloop.counter` sobre
  `resultado.personas`, `regla` y `ortografia`). El servicio recorre las mismas listas de
  `resultado_de_corrida(corrida)` en el mismo orden.

## R5. Cuándo y cómo carga la vista (revisado durante la implementación)

- **Decision**: la página de resultado se renderiza como hoy. Alpine pide
  `GET .../vista/?corrida=<id>` (JSON).
  - Si no hay PDF de vista en caché, la vista deja un archivo
    `vista-<expediente>-<documento>-<sha16>.pedido` en `EXPEDIENTES_TEMP_DIR` y responde
    `PREPARANDO`.
  - El worker (`procesar_documentos`, después de `confrontar_automaticamente`) convierte los
    pedidos con `preparar_vistas()`. Si falla, deja un `.error` que la vista informa una vez como
    `CONVERSION`.
  - Alpine consulta cada 3 s durante 10 min como máximo.
  - Cada PNG se pide con `loading="lazy"`.
- **Rationale**: medido el 2026-10-02 en la máquina de desarrollo, LibreOffice tardó de 12 a 42 s
  con un perfil ya creado y más de 120 s con el perfil temporal nuevo que usa `_soffice`. Una
  petición web no puede esperar eso. El worker ya serializa el trabajo pesado, y es el mismo patrón
  de F24 (confrontación automática).
- **Alternatives considered**: conversión síncrona en la petición (descartada por la medición); un
  perfil de LibreOffice persistente (más rápido, pero choca entre procesos simultáneos); convertir
  todos los borradores al extraerlos (trabajo sin límite cada 24 h, al caducar la caché).

## R6. Colores y accesibilidad

- **Decision**: alta en rojo (`--sev-alta`, borde continuo, ícono de triángulo), media en amarillo
  ámbar (`--sev-media`, borde discontinuo, ícono de círculo) y baja en neutro gris azulado
  (`--sev-baja`, borde punteado, ícono de información). Relleno translúcido para que se lea el
  texto. La selección añade un contorno grueso y foco visible.
- Cada recuadro es un `<button>` con `aria-label` ("Severidad alta: <título>, página 3"). Avance y
  Retroceso de página cambian de página.
- **Rationale**: el color lo eligió el usuario; la doble codificación cumple el principio VIII y
  FR-002.

## R7. Auditoría

- **Decision**: no se añade un registro nuevo. La vista no cambia datos y la consulta del resultado
  (`documento_resultado`) tampoco se registra hoy. Se mantiene la misma política ("como cualquier
  consulta del resultado").

## R8. Cache del navegador

- **Decision**: el PNG y el JSON se sirven con `Cache-Control: no-store` y `X-Content-Type-Options:
  nosniff`. En los PCs compartidos de la notaría no deben quedar imágenes con datos personales en la
  caché del navegador.
