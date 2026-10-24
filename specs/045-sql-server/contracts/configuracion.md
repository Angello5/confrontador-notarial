# Contrato: configuración y creación de la base

## Variables de entorno del ERP

Se definen fuera del repositorio, en el entorno del servicio, igual que `DJANGO_SECRET_KEY`. Sustituyen a `POSTGRES_*`.

| Variable | Obligatoria | Por defecto | Uso |
|---|---|---|---|
| `DB_HOST` | no | `127.0.0.1` | Servidor de SQL Server (nombre o IP; instancia con nombre: `SERVIDOR\INSTANCIA`). |
| `DB_PORT` | no | `1433` | Puerto TCP. Se ignora con instancia con nombre. |
| `DB_NAME` | no | `confrontador` | Base del ERP. |
| `DB_USER` | no | `confrontador` | Login de SQL Server del ERP. |
| `DB_PASSWORD` | **sí** | — | Clave del login. Sin ella, `config/settings.py` lanza `ImproperlyConfigured` y el ERP no arranca. |
| `DB_TRUST_SERVER_CERTIFICATE` | no | apagada | `1`/`true`/`yes` para confiar en el certificado propio del servidor en la LAN. Apagada exige un certificado válido. |

Reglas:

- La conexión siempre va cifrada (ODBC Driver 18, `Encrypt=yes`).
- Ningún mensaje de error ni log incluye `DB_PASSWORD` ni la cadena de conexión.
- Las pruebas usan valores fijos solo de prueba (`tests/settings.py` y el CI), nunca los del servidor.

## Script `scripts/sqlserver/crear_base.sql`

Lo ejecuta el administrador con `sqlcmd` y una cuenta con permisos de servidor:

```text
sqlcmd -S <servidor> -E -b -v ERP_CLAVE="<clave>" -i scripts/sqlserver/crear_base.sql
```

| Paso | Resultado esperado | Si falla |
|---|---|---|
| 1. Versión | `SERVERPROPERTY('ProductMajorVersion') >= 13` (2016) | Error «Se necesita SQL Server 2016 o posterior» y se detiene. |
| 2. Edición | Muestra `SERVERPROPERTY('Edition')`; si contiene «Express», avisa del tope de 10 GB por base | Solo aviso; continúa. |
| 3. Base | `CREATE DATABASE confrontador COLLATE Modern_Spanish_100_CS_AS_SC` | Si ya existe, se detiene sin tocarla. |
| 4. Login | `CREATE LOGIN confrontador WITH PASSWORD = '$(ERP_CLAVE)', CHECK_POLICY = ON, DEFAULT_DATABASE = confrontador` | Si ya existe, se detiene. |
| 5. Usuario | `CREATE USER confrontador FOR LOGIN confrontador` y `ALTER ROLE db_owner ADD MEMBER confrontador`, solo en la base del ERP | — |

El script no crea roles de servidor ni toca otras bases (SR-001, SR-006). La clave no se escribe en el archivo.
