# Quickstart · F63 Base de datos en SQL Server

Guía para validar la fase en desarrollo y para instalar la base en el servidor de la notaría. Solo datos ficticios.

## 1. Requisitos

| Pieza | Desarrollo | Servidor SQLSERVER |
|---|---|---|
| SQL Server | Linux: contenedor `mcr.microsoft.com/mssql/server:2017-latest`. Windows sin Docker: SQL Server Express 2016 SP3 o posterior | SQL Server 2016 (edición por confirmar) |
| Driver | Microsoft ODBC Driver 18 for SQL Server | El mismo, en la máquina donde corra el ERP |
| Python | 3.13 con `requirements.txt` y `requirements-dev.txt` | 3.13 con `requirements.txt` |

## 2. Base de desarrollo

En Linux, con la misma colación que en producción:

```bash
docker run -d --name confrontador-sql -p 1433:1433 \
  -e ACCEPT_EULA=Y -e MSSQL_SA_PASSWORD='<clave-local-de-prueba>' \
  -e MSSQL_COLLATION=Modern_Spanish_100_CS_AS \
  mcr.microsoft.com/mssql/server:2017-latest
```

En Windows sirve cualquier SQL Server 2016 o posterior (Express o Developer). Las pruebas necesitan un login con el rol `dbcreator`, porque crean y borran su base. La base de pruebas se pone sola en compatibilidad 130, para comportarse como 2016 (`tests/conftest.py`).

Variables, fuera del repositorio (contrato en [contracts/configuracion.md](contracts/configuracion.md)):

```bash
export DJANGO_SECRET_KEY='<clave-local>' DB_USER=sa DB_PASSWORD='<clave-local-de-prueba>' DB_TRUST_SERVER_CERTIFICATE=1
```

## 3. Escenarios de validación

| # | Comando o acción | Resultado esperado | Cubre |
|---|---|---|---|
| 1 | `python manage.py migrate` | Aplica todas las migraciones sin errores | US1, US2 |
| 2 | `python scripts/generar_fixtures.py` y `python -m pytest` | Pasan las mismas pruebas que hoy (en Windows sin LibreOffice, todas salvo `test_legacy`) | SC-001 |
| 3 | `python -m pytest tests/test_procesamiento_concurrente.py` | La exclusión entre procesos funciona con dos conexiones y se libera al cerrar una | FR-006 |
| 4 | Prueba de unicidad del kardex | «K-100» dos veces activo: rechazado; «K-100» y «k-100»: aceptados | FR-003, FR-004 |
| 5 | Prueba de actividad semanal | Domingo y lunes caen en semanas distintas | SC-006 |
| 6 | Prueba de supresión de sentido | Marca como suprimidos los análisis de las corridas que usaron el texto | R6 |
| 7 | `python manage.py check --database default` contra un servidor anterior a 2016 (prueba con la versión simulada) | Error «Se necesita SQL Server 2016 o posterior» | FR-010 |
| 8 | Dos `procesar_documentos` con 20 documentos en cola, mientras se abre la lista de kardex | Ningún documento se procesa dos veces; la lista responde en menos de 2 s | SC-003, SC-004 |
| 9 | Medición privada del expediente de referencia (`-o addopts= -m local_reference --tb=no`), solo en local: está prohibida en el CI | 8 de 8, 0 falsos positivos y salida idéntica en 5 corridas | SC-002, FR-012 |
| 10 | Con `procesar_documentos --continuo` en marcha, reiniciar el servicio de SQL Server y subir un documento | El worker retoma la cola sin reiniciarlo | US3 (escenario 4) |

## 4. Instalación en el servidor (administrador de la notaría)

1. Instalar el ODBC Driver 18 en la máquina del ERP.
2. Ejecutar `scripts/sqlserver/crear_base.sql` con `sqlcmd`, pasando la clave por variable ([contrato](contracts/configuracion.md)). El script muestra la versión y la edición y avisa si es Express.
3. Configurar `DB_HOST`, `DB_NAME`, `DB_USER` y `DB_PASSWORD` en el entorno del servicio. Si el servidor usa un certificado propio, activar `DB_TRUST_SERVER_CERTIFICATE` de forma explícita.
4. `python manage.py migrate` y `python manage.py bootstrap_admin`.
5. Ingresar con la cuenta creada y confrontar un kardex ficticio.

Tiempo objetivo: menos de 30 minutos (SC-005).

## 5. Resultados (2026-10-24, Windows 10 con SQL Server 2025 Developer)

| Escenario | Resultado |
|---|---|
| Suite completa contra SQL Server (base de pruebas en compatibilidad 130, colación `Modern_Spanish_100_CS_AS`) | 943 passed, 9 skipped; solo falla `test_legacy`, que requiere LibreOffice y no está instalado en este equipo |
| `crear_base.sql` (T019) | Primera ejecución: base, login y usuario en 1 s. Segunda: se detiene con «ya existen» y no cambia nada. El login no tiene roles de servidor y no puede abrir otra base (error 916). `migrate` y `check --database default` con ese login, sin errores |
| SC-004 (T022): 507 kardex y un documento en extracción por el worker real | Peor de 5 peticiones: lista 0,66 s; estado 0,02 s; Inicio 0,11 s |
| Worker continuo sobre SQL Server | Procesó y confrontó los kardex ficticios; sobrevive a un corte de la base (`test_el_worker_continuo_sobrevive_a_un_corte_de_la_base`) |
| Medición privada del expediente de referencia (SC-002) | Pendiente: se corre en el equipo que tiene los expedientes locales |
