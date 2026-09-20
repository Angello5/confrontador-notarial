# Research: F4 · Expedientes

**Alcance de esta etapa**: decisiones técnicas para la implementación posterior.
No se modifica `spec.md` ni `data-model.md`; ambos son documentos aprobados y
las observaciones sobre ellos se registran al final.

## Decisiones

### Aplicación y límites

- **Decisión**: crear una aplicación Django nueva llamada `expedientes` y
  registrarla en el proyecto existente. `accounts/`, `core/`, `nucleo/` y el
  comportamiento de `adaptadores/extraccion.py` permanecen en sus límites
  actuales.
- **Alternativas descartadas**: añadir los modelos a `core/` o reestructurar
  `accounts/`; ambas opciones mezclan responsabilidades y contradicen el
  alcance explícito de F4. Crear una API o una SPA también se descarta porque
  la interfaz existente usa plantillas Django.

### Persistencia y restricciones

- **Decisión**: implementar las tres entidades ya definidas en
  `data-model.md`: `Expediente`, `Documento` y `TextoExtraido`. Las reglas de
  unicidad que afectan a concurrencia serán restricciones de PostgreSQL/Django:
  `Expediente.codigo`, `(expediente, rol, hash_archivo)` y
  `(hash_archivo, version_extractor)`.
- **Alternativa descartada**: comprobar unicidad solo en la vista o en
  `services.py`; una comprobación previa no protege dos peticiones simultáneas.
  Tampoco se crea un repositorio genérico sobre el ORM.

### Identidad del extractor y caché

- **Decisión**: exponer, con el cambio mínimo necesario, una función pública en
  `adaptadores/extraccion.py` que construya `version_extractor` a partir de
  `_OCR_FILES` y `_OCR_USE_CLS`, ordenados de forma determinista. La función no
  cambia `leer`, `_ocr`, `_cacheado` ni ningún resultado de extracción. La
  caché de F4 se indexa en la base de datos por `(hash_archivo,
  version_extractor)`; la caché de disco existente conserva su propia lógica.
- **Alternativas descartadas**: copiar los hashes en `expedientes` (duplica
  una fuente de verdad), usar solo la versión del paquete OCR (no cubre todos
  los recursos ni `use_cls`) o derivar la versión del nombre de un archivo de
  caché (es un detalle privado y no es una identidad estable).
- **Prueba exigida**: una prueba sintética debe demostrar que cambiar un hash o
  `_OCR_USE_CLS` cambia la identidad, y que la extracción existente mantiene el
  mismo comportamiento.

### Cola de extracción

- **Decisión**: `Documento.estado = PENDIENTE` es la cola. El comando
  `procesar_documentos` toma filas pendientes mediante una transacción y
  bloqueo de fila compatible con PostgreSQL, las pasa a `PROCESANDO`, y deja
  el trabajo de orquestación en `services.py` y el comando. Las vistas solo
  validan, llaman a servicios y renderizan.
- **Alternativas descartadas**: Celery, Redis, RabbitMQ, hilos dentro de la
  petición y una cola en memoria. Añaden servicios o pierden el estado al
  reiniciar, y están expresamente prohibidos.
- **Recuperación**: el diseño debe devolver a `PENDIENTE` una fila
  `PROCESANDO` que exceda el umbral de recuperación y registrar un error
  seguro si corresponde. El valor del umbral queda pendiente de aclaración;
  no se inventa en este plan.

### Archivos temporales y huérfanos

- **Decisión**: guardar el archivo solo en un directorio temporal explícito,
  fuera de `STATICFILES_DIRS` y de cualquier ruta servida, guardar su ruta
  controlada en `Documento.ruta_temporal` y borrarlo en `finally` tanto en
  éxito como en error. Una tarea diaria de Django elimina rutas huérfanas de
  más de 24 horas y limpia la referencia de la fila.
- **Alternativas descartadas**: usar `FileField` bajo `MEDIA_ROOT` servido por
  configuración genérica (facilita exposición accidental), mantener el
  binario en PostgreSQL o borrar solo en el camino exitoso (deja datos tras
  excepciones).
- **Límite de seguridad**: el nombre original nunca construye rutas. La ruta
  la genera el servicio con un nombre aleatorio/seguro y el directorio se
  configura fuera del árbol web.

### Validación de subida

- **Decisión**: validar en el servidor, antes de crear la fila y escribir el
  temporal, la extensión admitida, el tamaño máximo configurado y una firma o
  lectura de contenido coherente con el formato. Se reutilizan Django, la
  biblioteca estándar y dependencias ya fijadas (por ejemplo `zipfile`,
  `pymupdf`, `openpyxl` y Pillow donde corresponda); no se añade una librería
  de detección de MIME.
- **Alternativa descartada**: confiar en `Content-Type`, el nombre o la
  extensión enviados por el navegador; todos son datos no confiables.
- **Resultado**: archivos vacíos, corruptos o ilegibles pueden entrar en la
  cola si pasan la validación inicial y terminan en `ERROR` durante la
  extracción, sin traza ni contenido en el mensaje mostrado.

### Autorización

- **Decisión**: exigir autenticación y pertenencia a uno de los dos grupos ya
  definidos. `Usuario` solo puede consultar y modificar expedientes cuyo
  `creado_por` sea él; `Administrador` puede operar sobre todos. La regla se
  aplica en cada vista, endpoint JSON, reintento y comando accesible desde la
  aplicación, no solo en el menú.
- **Alternativa descartada**: paquete de permisos por objeto o una jerarquía
  de roles nueva; para dos roles y una regla de creador basta el ORM y los
  grupos existentes.

### Interfaz y estados

- **Decisión**: plantillas Django con los assets locales ya vendorizados y
  Alpine.js para consultar con `fetch` el endpoint JSON cada 2 segundos
  mientras haya documentos pendientes o procesándose. La respuesta contiene
  estados y contadores, nunca texto extraído ni contenido documental.
- **Alternativas descartadas**: HTMX, React, WebSockets y una API separada;
  introducen dependencias o infraestructura no permitida para este flujo.
- **Mensajes**: los textos son españoles, explican la acción siguiente y no
  incluyen nombre de archivo, texto, hash, ruta, traceback ni datos personales.

### Supresión del texto

- **Decisión**: ofrecer un comando de gestión para localizar el expediente,
  borrar el texto extraído según las reglas aprobadas y conservar hashes,
  fechas y filas documentales que deban permanecer. El comando será explícito,
  auditable por su resultado agregado y no imprimirá contenido.
- **Alternativa descartada**: borrar el expediente o el documento completo;
  no satisface el derecho de supresión descrito en la constitución y destruye
  metadatos requeridos.
- **Dependencia**: la semántica cuando un `TextoExtraido` está compartido por
  varios expedientes no queda determinada de manera compatible entre
  `spec.md` y `data-model.md`; se mantiene como `[NEEDS CLARIFICATION]`.

### Dependencias y calidad

- **Decisión**: no se cambia `requirements.in` ni los locks. Las pruebas se
  añaden a la suite pytest existente, con PostgreSQL del job `tests`, fixtures
  sintéticas y pruebas de integración para permisos, concurrencia, borrado
  temporal y comandos. Se mantienen Ruff, cobertura, `pip-audit`, gitleaks y
  SonarQube sin nuevos jobs.
- **Alternativa descartada**: SQLite para las pruebas de cola; no demuestra
  las mismas garantías de bloqueo que PostgreSQL. Añadir un worker externo o
  una dependencia de MIME también queda fuera.

## `[NEEDS CLARIFICATION]` pendiente

Estas preguntas deben resolverse antes de implementar las tareas afectadas:

1. **FR-011**: ¿cuál es el tamaño máximo en bytes, o dónde se configura su
   valor operativo? La spec exige un máximo configurable, pero no da número ni
   valor por entorno.
2. **Recuperación del worker**: ¿qué antigüedad convierte un documento
   `PROCESANDO` en recuperable? `data-model.md` menciona un tiempo límite, sin
   valor ni regla para distinguir una tarea lenta de una caída.
3. **Supresión compartida**: si varios expedientes apuntan al mismo
   `TextoExtraido`, ¿la supresión debe vaciar el texto compartido para todos,
   desvincular solo el expediente objetivo conservando la caché, o impedir la
   operación hasta una decisión del responsable? La spec pide avisar y no
   romper el otro expediente; el modelo permite que el texto se vacíe en la
   entidad compartida.
4. **Borrado de documentos**: la sección UX exige confirmación antes de
   eliminar un documento, pero no existe FR, escenario ni transición que
   defina una acción de eliminación. ¿F4 incluye eliminar documentos, o esa
   frase debe retirarse/trasladarse a otra fase?
5. **Cierre de expediente**: el modelo define `CERRADO` y la spec dice que un
   expediente cerrado no admite documentos, pero no define pantalla, permiso,
   transición ni mensaje para cerrarlo. ¿El cierre es F4 o queda para otra
   fase?

## Contradicciones u observaciones sobre documentos aprobados

- `spec.md` exige que la supresión de un texto compartido avise y no rompa al
  otro expediente, mientras `data-model.md` modela una única fila compartida
  cuyo campo `texto` queda vacío al suprimir. Se reporta sin modificar ninguno.
- `spec.md` exige confirmación al eliminar un documento sin definir la acción
  funcional correspondiente. Se reporta sin inventar una ruta ni un estado.
- El modelo define estados y recuperación de `PROCESANDO`, pero no define el
  umbral temporal. Se deja pendiente, no se fija en el plan.
- No se encontró otra contradicción bloqueante entre la constitución 1.6.0,
  el roadmap, los diagramas y los documentos F4 revisados.
