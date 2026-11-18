# Data model · F76

Sin entidades nuevas ni migraciones.

| Elemento | Cambio |
|---|---|
| `Documento.metricas` (JSON) | Claves nuevas: `openvino` (sí o no), `procesos` y `paginas`; todas numéricas o lógicas, sin contenido de documentos. Las anteriores no cambian. |
| `TextoExtraido.version_extractor` | Con OpenVINO la identidad incluye el motor y su versión; con el motor actual es la de antes. |
| Cola de documentos | Orden: borrador y minuta primero, después recaudos; dentro de cada grupo, por antigüedad. |

Estados de `Documento`: sin cambios (`PENDIENTE` → `PROCESANDO` → `LISTO` o `ERROR`; `PROCESANDO` → `PENDIENTE` si su proceso murió y pasó el tiempo límite).
