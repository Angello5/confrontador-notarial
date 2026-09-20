# Contrato de interfaz: F4 · Expedientes

Interfaz interna de plantillas Django. No se expone una API pública. Todas las
rutas requieren sesión autenticada y un grupo `Administrador` o `Usuario`;
las verificaciones se repiten en servidor aunque un enlace no aparezca en el
menú. Los ejemplos usan marcadores, nunca datos de personas ni contenido de
escrituras.

## Rutas y acceso

| Ruta y método | Acceso | Resultado |
|---|---|---|
| `/expedientes/` GET | Usuario o Administrador | Listado de expedientes visibles; el Usuario ve los propios y el Administrador todos. Incluye estado y cantidad agregada de documentos pendientes. |
| `/expedientes/` POST | Usuario o Administrador | Valida el código digitado, crea el expediente en `BORRADOR` y vuelve a la pantalla de detalle/listado con confirmación. Código vacío o repetido permanece en pantalla con explicación. |
| `/expedientes/<id>/` GET | Creador o Administrador | Detalle del expediente, formulario de subida, formatos admitidos, tamaño máximo configurado, estados y resumen. No muestra texto extraído. |
| `/expedientes/<id>/documentos/` POST | Creador o Administrador | Valida rol, formato, contenido y tamaño en servidor; registra hash y metadatos y encola `PENDIENTE`. Un duplicado del mismo hash y rol se rechaza sin duplicar. |
| `/expedientes/<id>/estado/` GET | Creador o Administrador | JSON mínimo para Alpine: estado del expediente, documentos visibles con identificador interno, rol, estado, error seguro y fechas/contadores necesarios para pintar avance. Nunca incluye texto extraído, ruta temporal ni contenido. |
| `/expedientes/<id>/documentos/<doc_id>/reintentar/` POST | Creador o Administrador | Solo para `ERROR`; limpia el motivo, devuelve el documento a `PENDIENTE` y confirma que se reintentará. En otro estado responde con error claro. |

La forma exacta del `<id>` es un identificador técnico sin mostrarlo como dato
personal. Un usuario sin permiso recibe la denegación estándar sin revelar si
el expediente de otra persona existe.

## Pantallas y estados

### Listado y alta

- Estado vacío: explica que aún no hay expedientes visibles y ofrece el campo
  «Código del expediente» y el botón «Crear expediente».
- Código: obligatorio, se recortan espacios extremos en servidor y no se
  autocompleta ni se genera.
- Éxito: «Expediente creado. Ahora puede cargar sus documentos.»
- Repetido: «Ese código ya está registrado. Ingrese otro código.» No se
  identifica a la persona o expediente asociado.

### Detalle y subida

- El formulario muestra dos opciones de rol: «Fuente» y «Borrador»; la ayuda
  explica que minuta y documentos del cliente son fuentes.
- Antes de enviar se indican extensiones admitidas y el límite de tamaño
  vigente, sin sustituir la validación server-side.
- Mientras no haya documentos: «Este expediente aún no tiene documentos.»
- Éxito: «Documento recibido. Quedó en cola para extraer su texto.»
- Formato/tamaño/contenido inválido: mensaje en lenguaje claro que indica qué
  revisar, sin nombre original, ruta, hash, traceback ni fragmento documental.
- Duplicado: «Ese archivo ya está registrado con este rol en el expediente.»
- Expediente cerrado: «El expediente está cerrado y no admite documentos.»
  La acción de cierre no se incluye hasta resolver la aclaración correspondiente.

### Avance

Los estados visibles son exactamente:

| Estado técnico | Texto de interfaz | Presentación y acción |
|---|---|---|
| `PENDIENTE` | «Pendiente» | En cola; se informa que será procesado. |
| `PROCESANDO` | «Procesando» | Trabajo en curso; se muestra avance agregado sin simular porcentaje. |
| `LISTO` | «Listo» | Texto disponible para F5; no se muestra su contenido en F4. |
| `ERROR` | «No se pudo procesar» | Motivo seguro y botón «Reintentar extracción». |

Mientras exista al menos un documento en `PENDIENTE` o `PROCESANDO`, Alpine
consulta el endpoint cada 2 segundos. Al alcanzar todos `LISTO`, detiene el
sondeo, muestra «Todos los documentos están listos» y habilita el enlace
conceptual a F5 solo cuando F5 exista. Tras recargar, la pantalla reconstruye
el estado desde la base de datos.

Si falla una consulta de estado, se muestra «No se pudo actualizar el estado.
Intente recargar la página.» sin borrar el último estado conocido ni exponer
la excepción.

## Mensajes transversales y accesibilidad

- Mensajes de éxito y error usan `role="status"`/`role="alert"` apropiado y
  conservan foco visible.
- Cada campo tiene etiqueta asociada, ayuda breve y error asociado; los
  controles se pueden usar con teclado y no dependen solo del color.
- La navegación conserva el layout AdminLTE 4 de F2, breadcrumbs y vocabulario
  español. No se cargan recursos externos ni CDN.
- Los mensajes nunca incluyen texto extraído, nombres completos, domicilios,
  identificadores personales, rutas del servidor, hashes ni trazas.

## Comandos operativos relacionados

No son rutas HTTP ni se ofrecen como pantallas administrativas propias:

- `python manage.py procesar_documentos`: consume documentos pendientes y
  aplica extracción, reutilización, guardado y `finally`.
- `python manage.py limpiar_temporales`: elimina temporales huérfanos de más
  de 24 horas según la política aprobada.
- `python manage.py suprimir_texto_expediente <codigo>`: solicita la supresión
  del texto asociado y conserva los metadatos definidos. Su comportamiento
  para texto compartido queda `[NEEDS CLARIFICATION]`.
