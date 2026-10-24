# Tasks: F63 · Base de datos en SQL Server

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/configuracion.md](contracts/configuracion.md), [quickstart.md](quickstart.md)

**Tests**: obligatorios por el principio III. Cada cambio de comportamiento empieza con una prueba que falla contra SQL Server (research R11).

**Formato**: `[ID] [P?] [Story] Descripción`. `[P]` indica que la tarea va en otro archivo y no depende de una tarea pendiente.

## Phase 1: Setup

- [x] T001 Enmendar la constitución a 2.1.0: Django + SQL Server con `mssql-django` y el ODBC Driver 18; la cola sobre la base del ERP (`.specify/memory/constitution.md`).
- [x] T002 Dependencias en `requirements.in`: añadir `mssql-django==1.8.0`, `pyodbc==5.3.0` y `pytz` (versión fijada); quitar `psycopg[binary]`. Regenerar `requirements.txt` con `--generate-hashes` y volver a añadir al final, a mano, `colorama` y `tzdata` para Windows (las exige `test_lockfile_pins_every_direct_requirement`). Regenerar `requirements-dev.txt`; `pip_audit --strict` limpio.
- [x] T003 Preparar un SQL Server de desarrollo según `specs/045-sql-server/quickstart.md` §2: colación `Modern_Spanish_100_CS_AS`, y un login de desarrollo con `dbcreator`.

## Phase 2: Foundational (bloquea todas las historias)

- [x] T004 [P] Prueba en `tests/test_foundation.py`: sin `DB_PASSWORD`, `manage.py check` falla y el mensaje no incluye ninguna clave (FR-009, SR-004). Debe fallar antes de T005.
- [x] T005 `config/settings.py`:
  - `DATABASES` con `"ENGINE": "mssql"`;
  - `DB_HOST` (`localhost`), `DB_PORT` (opcional, vacío), `DB_NAME` (`confrontador`), `DB_USER` (`confrontador`) y `DB_PASSWORD` obligatoria (`ImproperlyConfigured`);
  - `OPTIONS["driver"] = "ODBC Driver 18 for SQL Server"`, `Encrypt=yes` y `TrustServerCertificate=yes` solo si `DB_TRUST_SERVER_CERTIFICATE` vale `1`/`true`/`yes`;
  - `TEST["COLLATION"] = "Modern_Spanish_100_CS_AS"`.

  Contrato: `specs/045-sql-server/contracts/configuracion.md`.
- [x] T006 `tests/settings.py`: no hizo falta. `DB_PASSWORD` viene del entorno, en el CI y en local; una clave fija no serviría para dos servidores distintos.
- [x] T007 [P] `tests/test_procesamiento_concurrente.py`: `connection.vendor == "microsoft"` en lugar de `"postgresql"`. Las pruebas de exclusión deben fallar antes de T008.
- [x] T008 `expedientes/bloqueos.py`: `exclusivo` con `sp_getapplock` (`@Resource` = `notaria:` + el hash hexadecimal actual, `@LockMode='Exclusive'`, `@LockOwner='Session'`, `@LockTimeout=0`; obtenido si el retorno es `>= 0`) y `sp_releaseapplock` en `finally`. Actualizar el docstring (research R3). Lo usan el worker y la vista del borrador en cada vuelta, por eso bloquea todo lo demás.
- [x] T009 `.github/workflows/ci.yml`:
  - service container `mcr.microsoft.com/mssql/server:2017-latest` fijado por digest, con `ACCEPT_EULA=Y`, una clave `sa` solo de prueba, `MSSQL_COLLATION=Modern_Spanish_100_CS_AS` y healthcheck con `sqlcmd`;
  - compatibilidad 130 en la base de pruebas desde `tests/conftest.py` (`django_db_setup`), sin tocar `model`;
  - instalación de `msodbcsql18` (versión fijada) desde `packages.microsoft.com`;
  - `DB_*` en lugar de `POSTGRES_*`.
- [x] T010 `python manage.py migrate` contra el SQL Server de desarrollo: aplica `accounts`, `expedientes` (0001–0013) y Django sin errores.

**Checkpoint**: el ERP arranca sobre SQL Server y el worker puede tomar trabajo.

## Phase 3: User Story 1 · El personal trabaja igual que hoy (P1) 🎯 MVP

**Goal**: mismas pantallas, reglas y resultados sobre SQL Server.

**Independent Test**: suite completa contra SQL Server y medición del expediente de referencia.

- [x] T011 [P] [US1] Pruebas en `tests/test_sql_server.py`:
  - «K-100» activo dos veces: rechazado con el mensaje de `codigo_ocupado`;
  - archivado y nuevo activo «K-100»: aceptado;
  - «K-100» y «k-100» activos a la vez: aceptados («codigo único si `archivado_el IS NULL`», FR-003 y FR-004);
  - usuarios «ana» y «Ana»: distintos.
- [x] T012 [P] [US1] Prueba en `tests/test_sentido_expedientes.py`: `sentido.suprimir` marca `SUPRIMIDO` y vacía `anotaciones` en las corridas cuyo `entradas` contiene el par (`hash_archivo`, `version_extractor`), y no toca las demás. Debe fallar en SQL Server con `NotSupportedError`.
- [x] T013 [US1] `expedientes/sentido.py::suprimir`: filtrar en Python los `AnalisisSentido` no suprimidos (con `select_related("corrida")`) cuyo `corrida.entradas` incluye algún par, y actualizarlos por `pk__in`. Añadir el comentario `# shortcut: recorre los análisis en memoria; pasar a una tabla de entradas si superan ~50 000` (research R6).
- [x] T014 [US1] Ejecutar `python -m pytest` contra SQL Server y corregir en su origen cada fallo propio del motor (orden, colación, tipos). Registrar cada corrección en `specs/045-sql-server/research.md`.
- [ ] T015 [US1] Medición privada `-o addopts= -m local_reference --tb=no` contra SQL Server, en el equipo con los expedientes locales: 8 de 8, 0 falsos positivos y salida idéntica en 5 corridas (SC-002). Anotar el resultado en `specs/045-sql-server/quickstart.md`.

**Checkpoint**: US1 completa y medible.

## Phase 4: User Story 2 · El administrador instala la base (P1)

**Goal**: base y usuario propios en el SQL Server de la notaría, con guía y script.

**Independent Test**: seguir `quickstart.md` §4 en un SQL Server limpio.

- [x] T016 [US2] Prueba en `tests/test_sql_server.py` (después de T011, mismo archivo): con `connection.sql_server_version` simulado en 2014, el check de base de datos devuelve el error «Se necesita SQL Server 2016 o posterior»; con 2016, ninguno (FR-010).
- [x] T017 [US2] Check `@register(Tags.database)` en `core/apps.py` que compara `connection.sql_server_version` con 2016 (research R7).
- [x] T018 [P] [US2] `scripts/sqlserver/crear_base.sql` según `specs/045-sql-server/contracts/configuracion.md`:
  - comprueba la versión (`ProductMajorVersion >= 13`) y avisa si es Express;
  - `CREATE DATABASE ... COLLATE Modern_Spanish_100_CS_AS`;
  - `CREATE LOGIN ... CHECK_POLICY = ON` con la clave en `$(ERP_CLAVE)`;
  - usuario con `db_owner` solo en la base del ERP;
  - se detiene sin cambios si la base o el login ya existen.
- [x] T019 [US2] Validar el script en el SQL Server de desarrollo:
  - crea base, login y usuario;
  - una segunda ejecución no cambia nada;
  - el login no puede leer otra base (SR-006);
  - el ERP migra y permite ingresar con `bootstrap_admin`.

  Medir el tiempo de la instalación completa (SC-005).
- [x] T020 [P] [US2] Documentación: en `README.md` y `AGENTS.md`, `POSTGRES_*` pasa a `DB_*`, ODBC Driver 18 como requisito y enlace a `specs/045-sql-server/quickstart.md`.

**Checkpoint**: instalación reproducible.

## Phase 5: User Story 3 · Procesos a la vez sin repetir trabajo (P2)

**Goal**: cola sin duplicados y lecturas sin espera en SQL Server (la exclusión ya quedó en T008).

**Independent Test**: dos workers con 20 documentos y navegación simultánea.

- [x] T021 [P] [US3] Prueba en `tests/test_procesamiento_concurrente.py`: dos hilos con su propia conexión llaman a `tomar_pendiente` sobre 20 documentos `PENDIENTE` y ninguno sale repetido. La prueba repite el reparto 10 veces seguidas, con `pytest.mark.parametrize` sobre la ronda (FR-005, SC-003).
- [x] T022 [US3] Medir SC-004 en desarrollo: con 500 kardex ficticios y un documento en extracción, la lista, el estado de un kardex y el Inicio responden en menos de 2 s. Anotar el resultado en `specs/045-sql-server/quickstart.md`.
- [x] T023 [US3] Prueba en `tests/test_procesamiento_concurrente.py`: el worker `--continuo` sobrevive a un `OperationalError` en una vuelta y sigue en la siguiente (escenario 4 de US3). Antes moría con cualquier `DatabaseError`. Implementado en `expedientes/management/commands/procesar_documentos.py`: atrapa `DatabaseError`, descarta las conexiones y reintenta.

**Checkpoint**: concurrencia y recuperación equivalentes a las de hoy.

## Phase 6: User Story 4 · El CI prueba contra SQL Server (P2)

**Goal**: cada PR prueba contra SQL Server.

**Independent Test**: el PR de esta fase.

- [ ] T024 [US4] En el PR: comprobar que el job `tests` corre contra el contenedor de T009 con compatibilidad 130, que `ci-required` exige su resultado y que `dependencies` audita las dependencias nuevas. Corregir `.github/workflows/ci.yml` si algo no cuadra.

## Phase 7: User Story 5 · La semana sigue empezando en lunes (P3)

**Goal**: actividad semanal de lunes a domingo en hora de Lima.

**Independent Test**: confrontaciones ficticias en domingo y lunes.

- [x] T025 [US5] Prueba en `tests/test_sql_server.py` (después de T016, mismo archivo): corridas el domingo 23:00 y el lunes 00:30 (hora de Lima) quedan en semanas distintas en `actividad_semanal`, también tras `SET LANGUAGE Español` en la conexión (FR-008, SC-006). Si falla, corregir `expedientes/services.py::_kardex_por`.

## Phase 8: Polish & Cross-Cutting

- [x] T026 [P] `.claude/skills/actualizar-local/SKILL.md`: el contenedor de SQL Server sustituye a `confrontador-test-pg`.
- [x] T027 [P] `docs/roadmap.md`: entrada F63 con la decisión del usuario, SQL Server 2016, la edición por confirmar y el aviso de fin de soporte.
- [x] T028 Buscar con `grep -ri postgres` fuera de `specs/0[0-4]*` y del historial de la constitución: no debe quedar ninguna referencia operativa (FR-013).
- [x] T029 Puertas antes del PR: `ruff check`, `ruff format --check`, `pytest`, `pip_audit --strict` y `pre-commit run --all-files` en verde. Pasar el estado de `specs/045-sql-server/spec.md` a «implementado».

## Dependencies & Execution Order

- **Setup (T001–T003)** → **Foundational (T004–T010)** → historias.
- **US1** (T011–T015) y **US2** (T016–T020) dependen solo de Foundational y pueden ir en paralelo, salvo T011 → T016 → T025, que comparten `tests/test_sql_server.py`.
- **US3** (T021–T023) depende de Foundational. T021 y T023 comparten `tests/test_procesamiento_concurrente.py`: una tras otra.
- **US4** (T024) necesita el PR abierto con T009.
- **US5** (T025) depende de Foundational.
- **Polish** al final. T029 cierra.

## Parallel Example

```text
Tras T010, en paralelo:
  T011 [US1] tests/test_sql_server.py (colación y unicidad)
  T012 [US1] tests/test_sentido_expedientes.py (supresión)
  T018 [US2] scripts/sqlserver/crear_base.sql
  T020 [US2] README.md / AGENTS.md
  T021 [US3] tests/test_procesamiento_concurrente.py (cola)
```

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1. El ERP funciona igual sobre SQL Server, con el worker incluido, y la medición no retrocede.
2. US2: instalación reproducible para F8.
3. US3: cola, lecturas medidas y recuperación del worker.
4. US4 y US5 con el PR.
5. Polish y puertas de calidad.
