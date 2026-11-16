# Data model · F76

Sin entidades nuevas ni migraciones.

| Elemento | Cambio |
|---|---|
| `Documento.procesando_el` | Pasa a ser la hora del último avance: se renueva al terminar cada página, como mucho cada 30 s. El tiempo límite sigue contando desde ese valor. |
| `Documento.metricas` (JSON) | Claves nuevas: `motor`, `procesos` y `paginas_leidas`. Las anteriores no cambian. |
| `TextoExtraido.version_extractor` | Con OpenVINO la identidad incluye el motor y su versión; con el motor actual es la de antes. |
| Cola de documentos | Orden: borrador y minuta primero, después recaudos; dentro de cada grupo, por antigüedad. |

Estados de `Documento`: sin cambios (`PENDIENTE` → `PROCESANDO` → `LISTO` o `ERROR`; `PROCESANDO` → `PENDIENTE` si no hay avance durante el tiempo límite).
