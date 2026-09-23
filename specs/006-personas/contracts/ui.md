# Contrato de interfaz: F11 · Extracción por personas

Interfaz interna de plantillas Django. Reutiliza la ruta y la autorización de
F5; no expone API pública ni guarda observaciones. Los ejemplos son genéricos y
ficticios.

## Ruta y autorización

| Acción | Acceso | Resultado |
|---|---|---|
| POST de confrontación de un borrador | Creador del expediente o Administrador, sesión autenticada y CSRF | Ejecuta extracción por personas y reglas existentes en memoria. |
| Documento ajeno, no borrador o sin permiso | Denegación estándar | No revela si el documento existe ni sus datos. |

El navegador no envía fuentes, umbrales ni personas. El servidor carga los
textos y páginas disponibles de F4 y vuelve a comprobar estado, pertenencia y
rol.

## Estados previos

| Condición | Estado y mensaje |
|---|---|
| Hay CLIENTE, MINUTA y BORRADOR listos con páginas disponibles | `DISPONIBLE`: «Confrontar borrador». |
| Falta un rol | `NO_DISPONIBLE`: nombra el rol faltante. |
| Algún documento está pendiente o procesándose | `NO_DISPONIBLE`: «Espere a que termine la extracción de los documentos». |
| Hay error de extracción | `NO_DISPONIBLE`: «No se pudo procesar un documento. Elimínelo y vuelva a subirlo». |
| Texto o páginas no están disponibles | `NO_DISPONIBLE`: «Vuelva a subir el documento para extraer sus páginas». |
| Hay varias minutas o borradores | Cada borrador se confronta por separado; nunca se cruzan sus catálogos. |

Una fila F4 con texto antiguo pero páginas nulas no se trata como una página
única. F11 informa falta de páginas y pide re-subida para evitar asociaciones
entre documentos que F4 ya aplanó.

## Estados del resultado

| Estado | Presentación |
|---|---|
| `TRABAJANDO` | «Confrontando el borrador…» sin porcentaje inventado. |
| `RESULTADO` | Secciones de Personas, Regla y Ortografía, con recuentos. |
| `RESULTADO_SIN_OBSERVACIONES` | Mensaje de éxito; no se presenta como error. |
| `ADVERTENCIA_CORRESPONDENCIA` | Panel separado; conserva el diagnóstico histórico y oculta comparaciones de campo si este bloquea. |
| `REVISION_MANUAL` | Panel de advertencia para candidatos ambiguos, nombres similares o documentos conflictivos; no equivale a coincidencia. |
| `NO_DISPONIBLE` | Explica que hay que volver a subir el archivo o resolver el aprovisionamiento local. |
| `ERROR_SEGURO` | «No se pudo completar la confrontación. Intente nuevamente». Sin traza, ruta ni contenido. |

## Tabla de personas extraídas

Se muestra en `<details>` plegado por defecto, después de la autorización.
Cada persona aparece una vez, con:

| Columna | Contenido |
|---|---|
| Nombre | Nombre normalizado de la estructura del núcleo; si no es legible, «No identificado». |
| Documento | Documento de identidad asociado dentro del bloque; si falta, «Sin documento». |
| Procedencia | Nombre original ya autorizado y página, sin ruta del servidor. Puede haber varias. |
| Estado | `Confirmada`, `Sin documento` o `Revisión manual`; nunca se expresa una similitud como aprobación. |

La sección incluye recuentos seguros de páginas descartadas por `separador` y
`SISGEN` y de páginas `no clasificadas` (con archivo y página), sin mostrar el texto descartado. El
nombre del archivo se escapa como cualquier dato de usuario y no se escribe en
logs.

## Observaciones de identidad

Se añade un grupo `Personas` antes de `Regla` y `Ortografía`:

| Tipo | Mensaje mínimo |
|---|---|
| Documento cruzado | «El documento de esta persona no coincide con el documento asociado en las fuentes». Muestra hallado, esperado y procedencias al usuario autorizado. |
| Documento sin titular | «El documento no pertenece a una persona conocida en las fuentes». |
| Conflicto de lecturas | «Hay lecturas incompatibles del documento o nombre; requiere revisión manual». |
| Nombre parecido | No se genera aprobación automática; solo `REVISION_MANUAL` si la notaría define que debe mostrarse. |

La observación incluye página/procedencia de fuente y ubicación del borrador
solo cuando el valor se encuentra con la lógica de F5. No muestra el texto
completo de fuente o borrador.

## Compatibilidad con F5

- `Regla` sigue mostrando `NOMBRE`, `DNI`, `PARTIDA`, `MONTO` y `PARRAFO` con
  el formato de `specs/005-confrontacion/contracts/ui.md`.
- La proyección del nuevo `Catalogo` alimenta la salida histórica de regla;
  `PARTIDA`, `MONTO` y `PARRAFO` conservan sus observaciones y umbral.
- Las observaciones de persona se renderizan desde estructuras nuevas; nunca se
  parsea una cadena inventada ni se cambia el formato de `revisar()`.

## Privacidad y accesibilidad

- Solo usuarios autorizados ven nombres, documentos y procedencias.
- Logs y mensajes de error no contienen nombres, documentos, texto, rutas,
  hashes, identificadores de sesión ni trazas.
- La advertencia usa `role="alert"`; resultados y estados usan
  `role="status"`/`aria-live="polite"`.
- Las tablas tienen encabezados, los estados también tienen texto y el color
  no es la única señal; foco, teclado y orden de lectura siguen el layout
  AdminLTE 4 existente.
- Los estados `Sin documento` y `Revisión manual` no se presentan como
  coincidencias aprobadas.

## Decisiones aplicadas

- SISGEN se descarta completo, incluido `Documento Identificativo`.
- Un nombre sin documento se conserva y se verifica solo como nombre.
- Una página no clasificada se cuenta y lista por archivo y página, sin texto.
- Las páginas se unen con `\f` en la cadena plana; no hay migración. El texto
  histórico sin separador se procesa como un bloque.
