# Quickstart operativo: F4 · Expedientes

Esta guía usa únicamente archivos ficticios y una instalación local. Los
expedientes reales no se guardan en el repositorio ni en el directorio
temporal.

## Configuración

Configura `DJANGO_SECRET_KEY` fuera del repositorio y conserva las mismas
variables en cada terminal que ejecute Django.

| Variable | Valor por defecto | Uso |
|---|---:|---|
| `EXPEDIENTES_TEMP_DIR` | directorio temporal del sistema + `notaria-expedientes` | Directorio privado donde se guarda el archivo solo mientras se procesa. Debe ser una ruta absoluta. |
| `EXPEDIENTES_MAX_FILE_SIZE` | `26214400` bytes (25 MB) | Tamaño máximo aceptado antes de escribir el temporal. |
| `EXPEDIENTES_PROCESSING_TIMEOUT` | `900` segundos (15 minutos) | Tiempo tras el que un documento atascado en `PROCESANDO` vuelve a `PENDIENTE`. |

El directorio indicado por `EXPEDIENTES_TEMP_DIR` nunca puede estar bajo una
ruta servida por el servidor web ni incluirse en los respaldos. No uses para
él `static/`, `media/` ni una carpeta de expedientes respaldada.
Al crear el directorio, el sistema le asigna permisos `0700`, restringidos al
usuario del servicio, tanto con la ruta por defecto como con una configurada.

La carpeta local para archivos reales se llama `expedientes_locales/` y está
excluida por `.gitignore`. `expedientes/` es código Django versionado; no
coloques documentos allí.

## Tareas programadas

El worker se ejecuta con:

```bash
python manage.py procesar_documentos
```

Programa esta orden aproximadamente cada minuto (o con la frecuencia que
requiera la carga y el tiempo de extracción). Es seguro que dos ejecuciones se
solapen: la cola toma filas con `select_for_update(skip_locked=True)`, por lo
que cada ejecución salta las filas bloqueadas por la otra y no procesa dos
veces el mismo documento.

Ejecuta una vez al día:

```bash
python manage.py limpiar_temporales
```

La limpieza borra temporales referenciados con más de 24 horas que ya no están
en `PROCESANDO`, limpia su referencia en la fila y elimina también archivos
huérfanos del directorio temporal con más de 24 horas. No borra temporales
recientes ni el texto extraído.

Para atender una solicitud de supresión, ejecuta:

```bash
python manage.py suprimir_texto_expediente <codigo>
```

El comando vacía el texto extraído y conserva las filas, hashes, fechas,
autores y documentos. Si el texto está compartido, también lo vacía para los
demás expedientes que lo referencien; el comando informa únicamente el conteo
afectado. Tras la supresión un documento puede conservar estado `LISTO` con
texto vacío: la fase F5 debe tratarlo como texto no disponible y no
confrontarlo contra una cadena vacía.

## Flujo local completo con archivos ficticios

Desde la raíz del repositorio:

```bash
export DJANGO_SECRET_KEY='<clave-local-no-versionada>'
export EXPEDIENTES_TEMP_DIR="$(mktemp -d /tmp/expedientes-temporales.XXXXXX)"
mkdir -p expedientes_locales
printf '%s\n' 'Fuente ficticia para pruebas locales.' > expedientes_locales/fuente-ficticia.txt
printf '%s\n' 'Borrador ficticio para pruebas locales.' > expedientes_locales/borrador-ficticio.txt
python manage.py migrate
python manage.py bootstrap_admin
python manage.py runserver 127.0.0.1:8000
```

En `http://127.0.0.1:8000/`, inicia sesión con la cuenta local creada de
forma interactiva, crea un expediente con un código ficticio y carga los dos
archivos indicando `CLIENTE`, `MINUTA` y `BORRADOR`. En otra terminal, con las mismas
variables de entorno, ejecuta `python manage.py procesar_documentos`; la
pantalla debe pasar por `PENDIENTE`/`PROCESANDO` a `LISTO` y el directorio
temporal debe quedar vacío. Comprueba también eliminar un documento con
confirmación y, si necesitas probar la supresión, ejecuta el comando anterior
con el código ficticio.

La suite sintética y los gates locales se ejecutan así:

```bash
python scripts/generar_fixtures.py
python -m ruff check .
python -m ruff format --check .
python -m pytest --cov --cov-report=term --cov-report=xml:coverage.xml
```

No ejecutes la medición `local_reference` en CI ni copies sus archivos a
`expedientes_locales/`. Al terminar la prueba local, elimina los archivos
ficticios y el directorio temporal creado para la sesión.
