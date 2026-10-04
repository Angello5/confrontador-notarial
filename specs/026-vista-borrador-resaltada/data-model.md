# Data Model: F32 · Vista del borrador con errores resaltados

No hay modelos ni migraciones nuevas. Las estructuras siguientes existen en memoria o en la
respuesta JSON.

## Segmento (entrada del núcleo)

| Campo | Tipo | Regla |
|---|---|---|
| `texto` | str | texto tal como se lee en la página; no vacío |
| `x0, y0, x1, y1` | float | fracciones del ancho y del alto de la página, `0 ≤ x0 < x1 ≤ 1` |
| `linea` | int | identificador de la línea visual; segmentos de la misma línea, en orden de lectura |

Origen:

- PDF con texto: `page.get_text("words")`, con `linea` = índice de `(bloque, línea)`.
- OCR (Tramo B): `calidad.paginas[n].cajas`, ordenadas con `calidad_ocr.ordenar_filas`.

## Rectángulo (salida del núcleo)

| Campo | Tipo | Regla |
|---|---|---|
| `x0, y0, x1, y1` | float | fracciones de página, dentro del segmento de origen |
| `aparicion` | int | 0, 1, …: índice de la coincidencia en orden de lectura del documento |

`marcas(segmentos, valor) -> list[Rectangulo]`. Una coincidencia que cruza varias líneas produce
varios rectángulos con la misma `aparicion`. Es una función pura y determinista.

## Vista del borrador (respuesta del servicio)

| Campo | Tipo | Regla |
|---|---|---|
| `estado` | `"LISTA"` \| `"PREPARANDO"` \| `"NO_DISPONIBLE"` | `PREPARANDO`: pedido hecho, el worker aún no convierte |
| `motivo` | str \| null | solo si `NO_DISPONIBLE`: `FORMATO`, `SIN_ORIGINAL`, `VERIFICACION`, `CONVERSION`, `CORRIDA` |
| `paginas` | list[{`numero`, `proporcion`}] | `proporcion` = alto / ancho, para reservar el espacio antes de cargar el PNG |
| `marcas` | dict[`id_obs`, list[{`pagina`, `x0`, `y0`, `x1`, `y1`, `aparicion`}]] | `id_obs` ∈ `p<n>`, `r<n>`, `o<n>` |
| `no_ubicadas` | list[{`id`, `motivo`}] | `motivo` ∈ `AUSENTE` (sin línea en el borrador), `NO_EN_PAGINA` |

Los mensajes al usuario por `motivo` están en [contracts/vista-borrador.md](contracts/vista-borrador.md).

## Caché del PDF de vista (archivo)

- Ruta: `EXPEDIENTES_TEMP_DIR / f"vista-{expediente_id}-{documento_id}-{hash_archivo[:16]}.pdf"`.
- Se crea: el worker (`preparar_vistas`) lo crea para cada archivo `.pedido` que deja la vista
  JSON, tras verificar que el SHA-256 del original es igual a `Documento.hash_archivo`.
- Se borra: a las 24 h (`limpiar_temporales`, como huérfano), al eliminar el documento y con
  `suprimir_texto_expediente`. Lo mismo vale para `.pedido` y `.error` (`borrar_vistas`, llamado
  desde `borrar_originales`).
- Nunca aparece en respuestas, mensajes ni logs.

## Transiciones

`(sin caché) → .pedido → PREPARANDO → worker convierte → LISTA`. Si la conversión falla, el worker
deja `.error` y la vista responde una vez `NO_DISPONIBLE`/`CONVERSION`; la siguiente consulta lo
vuelve a pedir. La verificación del original (`VERIFICACION`) se comprueba en cada petición.
