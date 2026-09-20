# Data Model: F4 · Expedientes

Tres entidades nuevas en una aplicación Django `expedientes`. El diagrama de
entidades y el del flujo de procesamiento están en
`docs/arquitectura/f4-expedientes-modelo.mmd` y
`docs/arquitectura/f4-expedientes-flujo.mmd` (Mermaid: se leen en texto plano y
se abren en draw.io con Extras > Editar diagrama).

## Expediente

Un trámite de la notaría sobre el que se confrontan documentos.

| Campo | Tipo | Regla |
|---|---|---|
| `codigo` | texto corto, requerido, único | Lo digita el usuario al crear el expediente. El sistema no lo genera ni lo autocompleta. Se normaliza quitando espacios de los extremos. |
| `creado_por` | FK a la cuenta de usuario, requerido, PROTECT | Quien lo creó. Es quien puede verlo, además de cualquier Administrador. |
| `creado_el` | fecha/hora, automática | — |
| `actualizado_el` | fecha/hora, automática | — |

El expediente NO almacena un estado propio: se deriva del estado de sus
documentos al mostrarlo. Un campo derivado y almacenado a la vez se desincroniza;
derivarlo elimina esa clase de error. No existe un estado `CERRADO`: la notaría
no sabe cuándo termina un trámite.

## Documento

Un archivo subido a un expediente. El archivo en sí es temporal; esta fila es lo
que permanece.

| Campo | Tipo | Regla |
|---|---|---|
| `expediente` | FK a Expediente, requerido, CASCADE | — |
| `rol` | texto de opciones, requerido | `FUENTE` (minuta y documentos del cliente) o `BORRADOR` (el proyecto de escritura a revisar). El núcleo trata todas las fuentes como un solo conjunto frente al destino. |
| `nombre_original` | texto, requerido | Solo para mostrar. Dato no confiable: nunca se usa para construir una ruta. |
| `hash_archivo` | texto de 64, requerido, indexado | SHA-256 del contenido, calculado antes de procesar. |
| `tamano_bytes` | entero positivo, requerido | Se valida contra el máximo configurado antes de almacenar. |
| `estado` | texto de opciones, requerido | `PENDIENTE` al subir, `PROCESANDO` mientras el worker lo tiene tomado, `LISTO` con texto disponible, `ERROR` si falló. |
| `error` | texto, opcional, vacío por defecto | Motivo entendible del fallo. Nunca incluye datos personales, contenido del documento ni trazas internas. |
| `ruta_temporal` | texto, opcional, vacío por defecto | Ruta del archivo mientras espera y se procesa. Se vacía al borrar el archivo. Un valor no vacío con más de 24 h es un huérfano. |
| `texto_extraido` | FK a TextoExtraido, nullable, PROTECT | NULL hasta que la extracción termina. |
| `subido_por` | FK a la cuenta de usuario, requerido, PROTECT | — |
| `subido_el` | fecha/hora, automática | — |
| `procesado_el` | fecha/hora, nullable | Se fija al pasar a `LISTO` o a `ERROR`. |

Restricción: un mismo `hash_archivo` no se repite dentro del mismo expediente
con el mismo `rol`; subirlo otra vez se avisa en lugar de duplicar en silencio.

## TextoExtraido

La caché de resultados del OCR. Es lo que evita repetir la extracción y lo que
la constitución 1.6.0 autoriza a conservar indefinidamente.

| Campo | Tipo | Regla |
|---|---|---|
| `hash_archivo` | texto de 64, requerido | SHA-256 del archivo del que proviene el texto. |
| `version_extractor` | texto, requerido | Identidad de lo que produjo el texto: modelos de OCR y sus hashes, más la versión de la extracción. Un cambio en cualquiera de ellos cambia este valor. |
| `texto` | texto largo, requerido, puede quedar vacío | El texto extraído. Queda vacío tras una supresión a solicitud, incluso si otros expedientes compartían esa entrada: el objetivo de la supresión es que el dato personal desaparezca. Esos expedientes conservan hash y fechas, y vuelven a extraer si se les sube el archivo otra vez. |
| `creado_el` | fecha/hora, automática | — |
| `ultimo_uso_el` | fecha/hora, requerida | Se actualiza cada vez que un documento reutiliza esta entrada. |

Restricción: `(hash_archivo, version_extractor)` es único. Esa pareja es la
llave de la caché.

La versión del extractor DEBE formar parte de la llave. En F3 una caché
indexada solo por el hash del archivo devolvió texto de un modelo de OCR
anterior tras cambiar de v4 a v5; incluir la versión hace que la invalidación
ocurra sola.

## Transiciones

Documento: `PENDIENTE` → `PROCESANDO` → `LISTO` | `ERROR`. Desde `ERROR` se
puede volver a `PENDIENTE` con un reintento. Un `PROCESANDO` sin avance más allá
del tiempo límite vuelve a `PENDIENTE`, para que la caída del worker no deje
documentos atrapados.

Expediente: no tiene transiciones propias. Al mostrarlo se deriva: sin
documentos está vacío, con alguno en `PENDIENTE` o `PROCESANDO` está procesando,
con todos en `LISTO` está listo para confrontar, y si alguno quedó en `ERROR` se
señala para que el usuario reintente.

Eliminar un documento borra su fila y su archivo temporal si lo tuviera, pero
NUNCA borra el `TextoExtraido`: esa entrada puede estar en uso por documentos de
otros expedientes. Solo el comando de supresión toca el texto.

## Persistencia

- PostgreSQL, mediante migraciones de Django incluidas en el mismo cambio.
- El archivo original NO se persiste: vive en el directorio temporal, fuera de
  cualquier ruta servida por el servidor web, y se borra en un bloque `finally`.
- Lo que permanece: la fila del documento con su hash, y el texto en
  `TextoExtraido`.
