# Research: F4 · Expedientes

**Alcance de esta etapa**: decisiones técnicas para la implementación posterior.
`spec.md` y `data-model.md` son la fuente de verdad aprobada; esta investigación
mantiene sus decisiones y concreta cómo se probarán.

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
  seguro si corresponde. El umbral por defecto es 15 minutos y se configura en
  `settings`; una ejecución programada aplica la misma regla a todos los
  documentos recuperables.

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
- **Convención local**: la carpeta `expedientes/` contiene código Django
  versionado; los datos reales de la notaría deben guardarse en
  `expedientes_locales/`, que está excluida por `.gitignore`. Las reglas por
  extensión siguen bloqueando archivos documentales aunque se creen fuera de
  esa carpeta.

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

### Eliminación de documentos

- **Decisión**: F4 incluye eliminar un documento mediante una acción explícita
  con confirmación. Tras confirmar, se elimina la fila y el temporal que aún
  exista, pero nunca `TextoExtraido`: esa entrada puede estar referenciada por
  documentos de otros expedientes.
- **Alternativa descartada**: reutilizar la supresión de texto para eliminar
  documentos; son operaciones distintas y la supresión debe vaciar el texto
  compartido sin borrar metadatos documentales.

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
  borrar el texto extraído de las entradas asociadas y conservar hashes,
  fechas, autores y filas documentales. Si una entrada está compartida, se
  vacía para todos los expedientes que la referencian y el comando informa el
  número de expedientes afectados. El comando será explícito, auditable por su
  resultado agregado y no imprimirá contenido.
- **Alternativa descartada**: borrar el expediente o el documento completo;
  no satisface el derecho de supresión descrito en la constitución y destruye
  metadatos requeridos.
### Dependencias y calidad

- **Decisión**: no se cambia `requirements.in` ni los locks. Las pruebas se
  añaden a la suite pytest existente, con PostgreSQL del job `tests`, fixtures
  sintéticas y pruebas de integración para permisos, concurrencia, borrado
  temporal y comandos. Se mantienen Ruff, cobertura, `pip-audit`, gitleaks y
  SonarQube sin nuevos jobs.
- **Alternativa descartada**: SQLite para las pruebas de cola; no demuestra
  las mismas garantías de bloqueo que PostgreSQL. Añadir un worker externo o
  una dependencia de MIME también queda fuera.

## Coherencia de las decisiones aprobadas

- El límite por defecto es 25 MB y se puede ajustar en `settings`; la
  validación ocurre antes de crear la fila o escribir el temporal.
- Un `PROCESANDO` con más de 15 minutos se devuelve a `PENDIENTE`; el umbral
  es configurable y no se almacena como estado del expediente.
- La supresión vacía una entrada `TextoExtraido` compartida para todos sus
  expedientes y comunica solo el conteo afectado; hashes, fechas, autores y
  filas permanecen.
- Eliminar un documento requiere confirmación, borra su fila y temporal, y no
  borra `TextoExtraido`.
- `Expediente` no tiene estado almacenado ni acción de cierre; su resumen se
  deriva de los estados de sus documentos.
