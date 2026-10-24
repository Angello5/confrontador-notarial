# Contrato: instalación en el servidor

## `erp.env`

Archivo `C:\ProgramData\ConfrontadorNotarial\erp.env`, una línea `NOMBRE=valor` por variable; las líneas con `#` son comentarios. Plantilla sin claves en `scripts/windows/erp.env.ejemplo`.

| Variable | Uso |
|---|---|
| `DJANGO_SECRET_KEY`, `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_TRUST_SERVER_CERTIFICATE` | Como hoy (F63) |
| `DJANGO_ALLOWED_HOSTS` | El nombre interno del ERP, por ejemplo `erp.notaria.local` |
| `ERP_NOMBRE`, `ERP_LOGO`, `ERP_DIRECCION` | Marca de la notaría (F28, F29). El logo vive en `C:\ConfrontadorNotarial\staticfiles\marca\logo.png`, compartido entre versiones (`collectstatic` sin `--clear`), con `ERP_LOGO=/static/marca/logo.png` |
| `EXPEDIENTES_TEMP_DIR`, `EXPEDIENTES_ORIGINALES_DIR` | Como hoy |
| `ERP_REGISTROS_DIR` | **Nueva.** Carpeta de registros rotados; sin ella, consola |
| `ERP_ESTADO_DIR` | **Nueva.** Carpeta de los archivos de estado; sin ella, sin avisos |
| `RESPALDO_DIR` | **Nueva.** Carpeta de respaldos en otro disco |
| `IIS_CERTIFICADO` | **Nueva.** Huella del certificado enlazado al sitio, para leer su vencimiento |

`DJANGO_DEBUG` no se define: el modo de desarrollo queda apagado.

## Scripts `scripts/windows/`

| Script | Lo ejecuta | Hace |
|---|---|---|
| `iniciar.ps1 -Rol web` | HttpPlatformHandler | Lee `erp.env` y arranca `waitress` en `127.0.0.1:%HTTP_PLATFORM_PORT%`, con `url_scheme=https` y 8 hilos |
| `iniciar.ps1 -Rol worker` | Tarea «Confrontador · procesamiento» | Lee `erp.env` y ejecuta `procesar_documentos --continuo` |
| `iniciar.ps1 -Rol tarea -Comando <cmd>` | Tareas diarias | Lee `erp.env` y ejecuta un comando de `manage.py` (por ejemplo `limpiar_temporales`) |
| `respaldar.ps1` | Tarea diaria 02:00 | Ver research R5 |
| `restaurar.ps1 -Fecha AAAAMMDD [-Prueba]` | Desarrollador o administrador | Ver research R5 |
| `verificar.ps1` | Tarea cada 5 min, o a mano | Comprobación en un paso y avisos en el Visor de eventos (R7): web, worker, base, LibreOffice, capa de sentido, certificado, tope de memoria de SQL Server y espacio libre en disco (menos del 10 %) |
| `instalar.ps1 -Version <tag>` | Desarrollador, como administrador, una vez | Carpetas y ACL, origen del Visor de eventos, versión inicial, sitio de IIS y tareas programadas |
| `actualizar.ps1 -Version <tag>` / `-VolverA <tag>` | Desarrollador | Ver research R9 |
| `web.config` | IIS | HttpPlatformHandler → `iniciar.ps1 -Rol web`; `/static/` desde `staticfiles`; redirección HTTP→HTTPS; `stdoutLogEnabled=false`; páginas 502/503 → `mantenimiento.html` |
| `mantenimiento.html` | IIS, cuando la web no responde | Página estática en español, sin términos técnicos: «El sistema se está actualizando o no está disponible en este momento. Intente de nuevo en unos minutos.» |

Reglas:

- Ningún script recibe claves por argumento; todos las leen de `erp.env`.
- Los scripts no escriben datos personales en la consola ni en el Visor de eventos.
- Un error termina el script con código distinto de 0 y queda registrado en el Visor de eventos (origen `ConfrontadorNotarial`).

## Tareas programadas

| Tarea | Disparador | Cuenta | Reintentos |
|---|---|---|---|
| Confrontador · procesamiento | Al iniciar el sistema | Cuenta de servicio | Cada 1 min, hasta 999; sin límite de duración |
| Confrontador · diario | 02:00 | Cuenta de servicio | 3 veces cada 10 min |
| Confrontador · verificación | Cada 5 min | Cuenta de servicio | — |
