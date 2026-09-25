# Contrato de interfaz: F5 · Confrontación

Interfaz interna de plantillas Django. No se expone una API pública ni se
guarda el resultado. Todas las rutas requieren sesión autenticada y el grupo
`Administrador` o `Usuario`; además, el usuario debe ser creador del
expediente o Administrador. Los ejemplos usan valores ficticios y no muestran
contenido real.

## Ruta y acción

| Ruta y método | Acceso | Resultado |
|---|---|---|
| `/expedientes/<id>/documentos/<doc_id>/confrontar/` POST | Creador o Administrador, documento `BORRADOR` del expediente | Valida precondiciones, ejecuta el resultado en memoria y renderiza la pantalla para ese borrador. Requiere CSRF. |
| misma ruta con documento ajeno o que no es borrador | Denegado | Respuesta de denegación estándar; no revela si existe el documento. |

La vista no acepta umbral ni fuentes desde el navegador. Solo usa los
documentos persistidos de F4, obtiene el texto ya extraído y delega la
orquestación a `expedientes.services`. El resultado se descarta al terminar la
respuesta.

## Carga del expediente

El detalle presenta dos columnas con aire visual: a la izquierda, las zonas
«Documentos del cliente» (`CLIENTE`) y «Minuta» (`MINUTA`); a la derecha,
«Proyecto (borrador)» (`BORRADOR`). Cada zona tiene un formulario independiente
con selección múltiple, etiqueta «Obligatorio», formatos admitidos y tamaño
máximo visibles antes de seleccionar archivos. La validación es server-side por
archivo: los válidos quedan en cola y cada inválido se muestra con su nombre y
motivo. La lista de documentos cargados es breve y muestra nombre y estado, sin
tabla densa mientras no haya resultado.

## Disponibilidad de la acción

En el detalle del expediente se muestra una acción por cada documento con rol
`BORRADOR`:

| Condición | Acción y mensaje visible |
|---|---|
| Existe al menos un `CLIENTE`, una `MINUTA` y el borrador tiene texto disponible; todos están `LISTO` | Botón «Confrontar borrador». |
| Falta `CLIENTE`, `MINUTA` o `BORRADOR` | Acción no disponible. El mensaje nombra cada rol faltante: «Documentos del cliente», «Minuta» o «Proyecto (borrador)». |
| Una fuente o el borrador está `PENDIENTE`/`PROCESANDO` | Acción no disponible. «Espere a que termine la extracción de los documentos». |
| El texto requerido es nulo o vacío por supresión | Acción no disponible. «El texto de este documento ya no está disponible. Vuelva a subirlo para confrontar». |
| Hay un documento `ERROR` | Acción no disponible. «No se pudo procesar un documento. Elimínelo y vuelva a subirlo». |
| Hay varios borradores | Cada borrador listo tiene su propia acción y resultado; nunca se mezclan. |

La disponibilidad es una ayuda de interfaz, no una autorización: el servidor
repite todas las comprobaciones y devuelve denegación o un estado comprensible
si el estado cambió entre la carga y el POST.

El sondeo JSON del detalle incluye una lista segura por borrador con su
identificador, `disponible` y `mensaje`; no incluye nombre, ruta, hash ni texto.
La pantalla reemplaza esa lista en cada sondeo y muestra la acción en cuanto el
estado pasa a disponible, sin recargar la página.

## Estados del resultado

| Estado | Presentación | Acción siguiente |
|---|---|---|
| `TRABAJANDO` | «Confrontando el borrador…» mientras dura la petición; no se simula un porcentaje. | Esperar; no se persiste ni se crea archivo. |
| `ADVERTENCIA_CORRESPONDENCIA` | Panel de advertencia visualmente distinto: mensaje de `diagnostico()` y «No se muestran diferencias campo por campo». | Revisar que borrador y fuentes pertenezcan al mismo expediente. |
| `RESULTADO` con observaciones | Resultado exitoso con grupos y recuentos. | Corregir según cada observación. |
| `RESULTADO` sin observaciones | Estado vacío exitoso: «No se encontraron observaciones. El borrador concuerda con las fuentes y la ortografía revisada». | No tratarlo como error. |
| `NO_DISPONIBLE` | «No se puede confrontar porque el texto requerido no está disponible. Vuelva a subir el archivo». | Volver al expediente y cargar el archivo otra vez. |
| `ERROR_SEGURO` | «No se pudo completar la confrontación. Intente nuevamente». Sin traza, ruta, hash ni texto. | Reintentar o solicitar revisión administrativa. |

Si la respuesta tarda más de un segundo, la implementación mantiene visible el
estado `TRABAJANDO` durante el cálculo. No se requiere polling porque F5 no
crea un trabajo persistente ni guarda estado; el polling descrito arriba solo
consulta la extracción de F4 y la disponibilidad previa a la acción.

## Agrupación y forma de cada observación

La pantalla presenta dos grupos, siempre en este orden:

1. **Regla** — datos duros y comparación de párrafos; muestra el recuento.
2. **Ortografía** — palabras no aceptadas; muestra el recuento.

Cada fila de `Regla` contiene:

| Campo | Contenido |
|---|---|
| Campo | `NOMBRE`, `DNI`, `PARTIDA`, `MONTO` o `PARRAFO`. |
| Valor hallado | Valor encontrado en el borrador; para un faltante, «No aparece en el borrador»; para un párrafo alterado, «No aparece o fue alterado». |
| Valor esperado | Valor de la fuente cuando existe; para una ausencia sin candidato, «No coincide con ninguna fuente»; para párrafo, fragmento de fuente y porcentaje de coincidencia. |
| Ubicación | «Línea N» y fragmento corto del borrador si el valor se encuentra; «No ubicada» si no se encuentra. La línea se calcula en la aplicación buscando el valor en el texto original. |

La tabla de `Regla` no añade columnas vacías de «Motivo» o «Porcentaje». Si la
salida de un párrafo trae una coincidencia, se muestra como detalle junto al
valor esperado; los motivos de ortografía se muestran en su propia tabla. Una
`FALTA` que duplica el valor esperado de una discrepancia del mismo campo se
consolida en una sola fila; las faltas sin equivalente se mantienen.

Cada fila de `Ortografía` contiene:

| Campo | Contenido |
|---|---|
| Palabra | Palabra marcada por el núcleo. |
| Motivo | «tilde mal puesta» o «no existe en castellano». |
| Sugerencia | Sugerencia del núcleo o «Sin sugerencia» cuando devuelve `?`. |
| Ubicación | Línea y fragmento corto del borrador, calculados en la aplicación. |

## Verificación de extracción

Después de un resultado de confrontación se muestra una sección `<details>`
plegada por defecto, titulada «Qué se extrajo de los documentos». Presenta el
catálogo agregado en el orden `NOMBRE`, `DNI`, `PARTIDA`, `MONTO` y, para cada
fuente, su nombre original, la cantidad de caracteres extraídos y el catálogo
que aportó al pasar su texto por `nucleo.verificar.catalogo()` por separado.
Una fuente sin valores en los cuatro campos muestra la señal visible «No
aportó campos detectables». Nunca se muestra el texto extraído completo.

Este resumen forma parte únicamente de la respuesta HTML de la acción de
confrontación para el creador del expediente o un Administrador. El endpoint de
sondeo conserva su contrato seguro y no devuelve catálogo, aportes, conteos de
caracteres ni texto extraído.

La aplicación adapta la salida actual de regla (`list[str]`) con el formato
documentado en `research.md`; no se muestra la cadena cruda al usuario. Las
tuplas de ortografía se mapean directamente a las columnas anteriores.

Un valor repetido muchas veces genera una sola observación. Los grupos solo se
renderizan si tienen filas, excepto que el estado `RESULTADO` puede mostrar
ambos recuentos en cero para dejar claro que no hubo hallazgos.

## Mensajes de seguridad, privacidad y accesibilidad

- Mensajes y logs no contienen DNI, nombres, domicilios, fragmentos completos,
  hashes, rutas, identificadores de sesión ni trazas.
- El fragmento de cada fila se limita a la evidencia necesaria para corregir
  y solo aparece después de la autorización. No se muestra el texto completo
  de fuentes ni borradores.
- El aviso de correspondencia usa `role="alert"`; resultados, estados vacíos y
  confirmaciones usan `role="status"` o `aria-live="polite"` según corresponda.
- Todas las columnas tienen encabezados y cada botón tiene texto; la acción se
  puede operar con teclado, mantiene foco visible y no depende solo del color.
- Se conserva el layout AdminLTE 4 de F2, breadcrumbs, vocabulario español y
  assets locales sin CDN.
