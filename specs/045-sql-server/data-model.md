# Data Model: F63 · Base de datos en SQL Server

El modelo de datos **no cambia**: mismos modelos, campos, restricciones y migraciones (0001–0013 de `expedientes`, las de `accounts` y las de Django). Las migraciones solo usan el ORM y `RunPython`, así que se aplican igual en SQL Server. Este documento registra cómo se representa cada pieza en el motor nuevo y qué hay que comprobar.

## Base

| Aspecto | Valor |
|---|---|
| Colación de la base | `Modern_Spanish_100_CS_AS_SC` (research R2) |
| Aislamiento | READ COMMITTED con bloqueos (por defecto); `READ_COMMITTED_SNAPSHOT` apagado (research R4) |
| Primer día de la semana | `DATEFIRST 7` por conexión, fijado por el conector (research R5) |
| Fechas | `datetime2` en UTC (`USE_TZ = True`), mostradas en `America/Lima` |
| Textos | `nvarchar(n)` y `nvarchar(max)` (UTF-16): tildes, «ñ» y comillas tipográficas sin pérdida |

## Restricciones que dependen del motor

| Modelo | Restricción | En SQL Server | Comprobación |
|---|---|---|---|
| `Expediente` | `expediente_codigo_activo_unico` (`codigo` único si `archivado_el IS NULL`) | Índice único filtrado | «K-100» activo dos veces: rechazado; uno archivado y otro activo: aceptado; «K-100» y «k-100»: aceptados (FR-003) |
| `TextoExtraido` | `texto_hash_version_unicos` (`hash_archivo`, `version_extractor`) | Índice único; clave de 192 caracteres (384 bytes), por debajo del límite de 900 bytes | Prueba existente de reutilización del texto |
| `Documento` | `documento_expediente_rol_hash_unicos` | Índice único | Prueba existente de documento duplicado |
| `Documento` | `documento_tamano_positivo` (`tamano_bytes > 0`) | `CHECK` | Prueba existente |
| `accounts.User` | `username` único | Índice único, sensible a mayúsculas por la colación | El login distingue mayúsculas como hoy |

## Campos JSON

`TextoExtraido.calidad`, `Documento.metricas`, `Corrida.entradas`, `Corrida.presentacion`, `DecisionCorreccion.correcciones_excluidas`, `.apariciones`, `.correcciones_no_aplicadas` y `AnalisisSentido.anotaciones` se guardan como `nvarchar(max)` validado con `ISJSON`, lo que exige SQL Server 2016 o posterior.

- Lectura y escritura completas: sin cambios.
- Lookups por contenido (`__contains`): no soportados. Único uso: `expedientes/sentido.py::suprimir`, que se reescribe (research R6).

## Bloqueos de aplicación (sin tabla)

`sp_getapplock` / `sp_releaseapplock` con recurso `notaria:<hash>` de la clave `notaria:{tipo}:{identidad}`. No crean filas: viven en el gestor de bloqueos de SQL Server y se liberan al cerrar la sesión (research R3).
