# Research: F63 · Base de datos en SQL Server

No quedan `[NEEDS CLARIFICATION]` en la spec. Las decisiones salen del código del ERP y del código fuente de `mssql-django` 1.8.0 (`mssql/base.py`, `operations.py`, `features.py`, `creation.py`).

## R1. Conector

- **Decision**: `mssql-django` 1.8.0 con `pyodbc` 5.3 y el Microsoft ODBC Driver 18 instalado en cada máquina. `mssql-django` 1.8.0 trae `pytz` como dependencia.
- **Rationale**: es el backend oficial de Microsoft. La 1.8.0 es la última que soporta SQL Server 2016 (tabla «Supportability» de su README: 2016–2025) y admite Django 5.2. La 2.0 exige SQL Server 2017 o posterior. Las tres dependencias nuevas no tienen vulnerabilidades conocidas (`pip-audit`, 2026-10-24).
- **Alternatives considered**: `mssql-django` 2.0 (no admite 2016); `django-pyodbc-azure` (abandonado); SQL a mano sin ORM (rompe el principio V).
- **Ruta de actualización**: cuando la notaría pase a SQL Server 2017 o posterior, se sube a la rama 2.x en un PR propio.

## R2. Mayúsculas y tildes (FR-003)

- **Decision**: la base del ERP se crea con la colación `Modern_Spanish_100_CS_AS_SC`, que distingue mayúsculas (CS) y tildes (AS). La base de pruebas usa la misma, vía `DATABASES["default"]["TEST"]["COLLATION"]`, y el contenedor del CI también (`MSSQL_COLLATION`).
- **Rationale**: SQL Server se instala por defecto sin distinguir mayúsculas. Con una colación CI, «K-100» y «k-100» chocarían en la unicidad del kardex, y los usuarios también. Hoy son distintos. El orden español coloca la «ñ» después de la «n».
- **Alternatives considered**: la colación por defecto del servidor (cambia el comportamiento); `Latin1_General_100_CS_AS_SC` (orden inglés).
- **Riesgo**: `tempdb` usa la colación del servidor. Django no crea tablas temporales; si alguna consulta llegara a mezclar colaciones, se corrige con `COLLATE DATABASE_DEFAULT` en esa consulta.

## R3. Exclusión entre procesos (FR-006)

- **Decision**: `expedientes/bloqueos.py` usa `sp_getapplock` (`@LockMode='Exclusive'`, `@LockOwner='Session'`, `@LockTimeout=0`) y `sp_releaseapplock`, con la misma clave derivada de `notaria:{tipo}:{identidad}`.
- **Rationale**: es el equivalente directo de `pg_try_advisory_lock`. El bloqueo pertenece a la sesión, no espera (el valor de retorno dice si se obtuvo) y SQL Server lo libera si la conexión muere.
- **Alternatives considered**: una tabla de bloqueos con filas (hay que limpiarla si muere el proceso); archivos de bloqueo (no sirven entre máquinas y quedan huérfanos).

## R4. Cola del worker y lecturas concurrentes (FR-005, FR-007)

- **Decision**: se mantiene `select_for_update(skip_locked=True)`, que `mssql-django` traduce a `WITH (ROWLOCK, UPDLOCK, READPAST)`, con el aislamiento por defecto de SQL Server (READ COMMITTED con bloqueos). **No** se activa `READ_COMMITTED_SNAPSHOT`.
- **Rationale**: SQL Server no admite `READPAST` en READ COMMITTED cuando `READ_COMMITTED_SNAPSHOT` está activado ([Table Hints](https://learn.microsoft.com/en-us/sql/t-sql/queries/hints-transact-sql-table)), así que activarlo rompería la cola. Sin él, una lectura solo espera a una transacción de escritura abierta. Las transacciones del worker son cortas: el OCR y la confrontación corren fuera de transacción (`_extraer_o_reutilizar` abre una antes y otra después del extractor; `tomar_pendiente` solo marca la fila). La espera queda en milisegundos y la mide SC-004.
- **Alternatives considered**: `READ_COMMITTED_SNAPSHOT` (incompatible con `READPAST`); aislamiento SNAPSHOT solo para las vistas (dos niveles de aislamiento y más configuración, sin necesidad medida).

## R5. Semana desde lunes y hora de Lima (FR-008)

- **Decision**: no hace falta código. `mssql-django` ejecuta `SET DATEFIRST 7` en cada conexión (`base.py`, opción `datefirst`), y su fórmula de `TruncWeek` lleva cada fecha al lunes con ese valor, sea cual sea el idioma del login o del servidor. La zona horaria se aplica como un desfase fijo calculado con `pytz`. Para `America/Lima` (UTC−5, sin horario de verano) es exacto.
- **Rationale**: queda cubierto por una prueba con confrontaciones ficticias en domingo y lunes (SC-006).
- **Alternatives considered**: forzar el idioma del login a `us_english` (no hace falta, porque `DATEFIRST` se fija por conexión).

## R6. Datos estructurados (JSON)

- **Decision**: los 8 `JSONField` funcionan en SQL Server 2016 (`supports_json_field` exige 2016 o posterior: `nvarchar(max)` validado con `ISJSON`). La única consulta que usa un lookup no soportado es `expedientes/sentido.py::suprimir`, con `corrida__entradas__contains` (`supports_json_field_contains = False`). Se reescribe filtrando en Python las corridas con análisis de sentido.
- **Rationale**: `suprimir` es el derecho de supresión de la Ley 29733: no puede fallar. El volumen es de cientos o pocos miles de análisis, que caben en memoria. Se marca con `shortcut:` y el punto en el que conviene cambiarlo.
- **Alternatives considered**: `OPENJSON` en SQL a mano (SQL propio del motor dentro del servicio); una columna o tabla nueva con los hashes de entrada (cambio de esquema que hoy no se justifica).

## R7. Versión mínima (FR-010)

- **Decision**: un check de Django con la etiqueta `database` en `config/apps.py` que falla si `connection.sql_server_version < 2016`, con el mensaje «Se necesita SQL Server 2016 o posterior». Corre con `migrate` y con `check --database default`.
- **Rationale**: `mssql-django` acepta 2005–2014 y solo fallaría más tarde, con el mensaje poco claro de `JSONField` (fields.E180).
- **Alternatives considered**: confiar en fields.E180 (el mensaje no dice qué versión instalar).

## R8. Configuración de la conexión (FR-009, SR-002–SR-004)

- **Decision**: variables `DB_HOST`, `DB_PORT` (1433), `DB_NAME`, `DB_USER` y `DB_PASSWORD` en lugar de `POSTGRES_*`, más `DB_TRUST_SERVER_CERTIFICATE`, apagada por defecto. El ODBC Driver 18 cifra la conexión por defecto (`Encrypt=yes`). Sin `DB_PASSWORD` el ERP no arranca, igual que sin `DJANGO_SECRET_KEY`. Contrato en [contracts/configuracion.md](contracts/configuracion.md).
- **Rationale**: los nombres neutros no atan la configuración al motor, y la confianza en un certificado propio de la LAN queda explícita (SR-003).
- **Alternatives considered**: conservar `POSTGRES_*` (engañoso); una cadena ODBC completa en una sola variable (más fácil filtrar la clave en un log).

## R9. CI (FR-012)

- **Decision**: el service container pasa a `mcr.microsoft.com/mssql/server:2017-latest`, fijado por digest, con `ACCEPT_EULA=Y`, una clave `sa` solo de prueba y `MSSQL_COLLATION=Modern_Spanish_100_CS_AS_SC`. Antes de las pruebas, un paso fija el nivel de compatibilidad de la base `model` en 130 (el de SQL Server 2016), para que la base de pruebas, que la copia, se comporte como 2016. El ODBC Driver 18 se instala desde el repositorio firmado de Microsoft (`packages.microsoft.com`) en una versión fijada.
- **Rationale**: SQL Server 2016 no tiene imagen para Linux; 2017 es la más antigua, y con el nivel de compatibilidad 130 emula el T-SQL de 2016. Las pruebas se conectan como `sa` porque pytest-django crea y borra la base de pruebas.
- **Alternatives considered**: un runner Windows con SQL Server 2016 instalado (lento y difícil de reproducir); probar en 2022 (no detectaría lo que 2016 no tiene).

## R10. Desarrollo local

- **Decision**: en Linux, el mismo contenedor del CI. En Windows sin Docker, SQL Server Express (2016 SP3 o posterior, con la base de pruebas en compatibilidad 130) y el ODBC Driver 18. La guía queda en [quickstart.md](quickstart.md).
- **Rationale**: un solo motor en todos los entornos (FR-013).

## R11. Pruebas afectadas

- `tests/test_procesamiento_concurrente.py` comprueba `connection.vendor == "postgresql"`; pasa a `"microsoft"`, el `vendor` de `mssql-django`.
- Pruebas nuevas, primero en rojo:
  - unicidad sensible a mayúsculas («K-100» y «k-100» conviven);
  - semana de domingo a lunes;
  - `suprimir` sin lookup JSON;
  - check de versión mínima;
  - lecturas sin espera mientras el worker escribe.

## R12. Instalación en SQLSERVER (FR-011, SR-001, SR-006)

- **Decision**: el script T-SQL `scripts/sqlserver/crear_base.sql` hace esto:
  - comprueba la versión (2016 o posterior) y la edición (avisa si es Express);
  - crea la base con la colación de R2;
  - crea el login con `CHECK_POLICY = ON`;
  - crea su usuario en esa base con el rol `db_owner` **solo en ella** y sin roles de servidor.

  El administrador lo ejecuta con `sqlcmd`, con la clave pasada por variable, nunca escrita en el archivo.
- **Rationale**: las migraciones necesitan DDL en su propia base. `db_owner` acotado a la base del ERP es el mínimo práctico, y la separación con las otras bases la da el propio SQL Server.
- **Alternatives considered**: `db_ddladmin` + `db_datareader` + `db_datawriter` (tres roles para el mismo resultado práctico); usar `sa` (rompe SR-001).
