# Implementation Plan: F63 · Base de datos en SQL Server

**Branch**: `feat/f63-sql-server` | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

## Summary

El ERP pasa de PostgreSQL a SQL Server 2016, el motor del servidor SQLSERVER, sin cambiar su comportamiento. El modelo de datos y las migraciones no cambian. Cambian cinco cosas:

- el conector: `mssql-django` 1.8.0, la última versión con soporte para 2016;
- la exclusión entre procesos: `sp_getapplock`;
- la supresión de la capa de sentido, que no puede filtrar dentro del JSON;
- un check de versión mínima;
- la configuración, el CI y las guías.

La base se crea con una colación que distingue mayúsculas y tildes, para que la unicidad del kardex y de los usuarios quede como hoy. Detalle en [research.md](research.md).

## Technical Context

- **Language/Version**: Python 3.13.
- **Primary Dependencies**:
  - Django 5.2 LTS;
  - nuevas: `mssql-django` 1.8.0, `pyodbc` 5.3 y `pytz` (dependencia del conector);
  - se retira `psycopg[binary]`;
  - del sistema: Microsoft ODBC Driver 18 for SQL Server.
- **Storage**: SQL Server 2016, base propia `confrontador` con colación `Modern_Spanish_100_CS_AS`. Sin cambios de esquema ([data-model.md](data-model.md)).
- **Testing**:
  - pytest y pytest-django contra SQL Server 2017 en contenedor, con la base de pruebas en compatibilidad 130 (2016);
  - en Windows, SQL Server Express;
  - la medición privada del expediente de referencia, contra SQL Server.
- **Target Platform**: SQLSERVER (Windows Server 2019) con SQL Server 2016. El mecanismo de despliegue sigue en F8.
- **Project Type**: monolito Django on-premise.
- **Performance Goals**: lista, estado y confrontación en menos de 2 s con 500 kardex mientras el worker escribe (SC-004).
- **Constraints**:
  - SQL Server 2016 fuera de soporte extendido desde el 2026-07-14;
  - sin `READ_COMMITTED_SNAPSHOT`, porque rompe `READPAST` (research R4).
- **Scale/Scope**: hasta 10 usuarios y un servidor. Unos 15 archivos tocados, sin pantallas nuevas.

## Constitution Check

| Principio | Cómo se cumple |
|---|---|
| I. Determinismo | El núcleo no cambia. SC-002 exige la misma medición (8 de 8, 0 falsos positivos y salida idéntica). |
| II. Núcleo puro | Ningún cambio en `nucleo/`. Lo específico del motor queda en `expedientes/bloqueos.py`, `expedientes/sentido.py` (orquestación) y `config/`. |
| III. Pruebas primero | Cada cambio de comportamiento empieza con una prueba que falla en SQL Server: colación, semana, supresión, versión y bloqueo (research R11). |
| IV. Privacidad | Mismos datos, en una base propia. La supresión de sentido sigue funcionando (R6). La clave y la cadena de conexión no van a logs ni al repositorio. Los respaldos, en F8. |
| V. Simplicidad | Un solo motor. Sin abstracción de base de datos ni capa nueva: se cambia el conector y tres puntos concretos. |
| VI. Seguridad | Login propio con `CHECK_POLICY`, `db_owner` solo en su base, sin roles de servidor. Conexión cifrada; la confianza en un certificado propio es explícita. |
| VII. DevSecOps | CI contra SQL Server, con la imagen fijada por digest y el driver ODBC desde el repositorio firmado de Microsoft. `pip-audit` cubre las dependencias nuevas, todas con hash. |
| VIII. Usabilidad | Ninguna pantalla cambia; los errores de base siguen con el mensaje genérico. |
| Restricciones técnicas | Constitución 2.1.0 (enmendada en esta rama): Django + SQL Server con `mssql-django` y el ODBC Driver 18; cola sobre la base del ERP. |

Resultado: sin violaciones.

## Estructura

```text
config/settings.py                    # DATABASES con mssql-django y DB_*; DB_PASSWORD obligatoria
core/apps.py                          # check de versión mínima (Tags.database)
expedientes/bloqueos.py               # sp_getapplock / sp_releaseapplock
expedientes/sentido.py                # suprimir() sin lookup JSON
scripts/sqlserver/crear_base.sql      # base, login y usuario del ERP (contracts/configuracion.md)
requirements.in, requirements.txt     # + mssql-django, pyodbc, pytz; − psycopg (tzdata/colorama al final, a mano)
tests/conftest.py                     # compatibilidad 130 en la base de pruebas
tests/test_procesamiento_concurrente.py   # vendor "microsoft"
tests/test_sql_server.py              # colación, semana, versión mínima
tests/test_sentido_expedientes.py     # supresión sin lookup JSON
.github/workflows/ci.yml              # service container SQL Server 2017, compat 130, ODBC 18
README.md, AGENTS.md                  # POSTGRES_* → DB_*, requisitos
.claude/skills/actualizar-local/SKILL.md  # contenedor de SQL Server en lugar del de PostgreSQL
docs/roadmap.md                       # entrada F63
```

## Complexity Tracking

| Complejidad | Por qué | Alternativa descartada |
|---|---|---|
| Tres dependencias nuevas (`mssql-django`, `pyodbc`, `pytz`) y un driver del sistema | Es el único backend oficial de Django para SQL Server; la notaría exige el motor. | Conector propio o SQL a mano. |
| Conector en una versión anterior (1.8.0) | La 2.0 no admite SQL Server 2016. | Exigir a la notaría actualizar SQL Server antes de F8 (decisión suya, fuera del alcance). |
| CI en SQL Server 2017 en compatibilidad 130 | No hay imagen Linux de 2016. | Runner Windows con 2016 instalado. |

## Riesgos

- **SQL Server 2016 sin parches de seguridad** desde el 2026-07-14, salvo con ESU. Se informa a la notaría; el ERP queda listo para 2017+ (FR-010).
- **Colación de `tempdb`** distinta a la de la base: no la usa el ERP; si aparece un conflicto, `COLLATE DATABASE_DEFAULT` en la consulta.
- **Espera de lecturas** por bloqueos: transacciones cortas; SC-004 lo mide. Si no se cumple, se revisa el aislamiento solo para las vistas de consulta.
- **Edición Express**: tope de 10 GB por base; el script lo detecta y F8 lo revisa con el respaldo.
