# Data Model: F8 · Despliegue

**No cambia el esquema de la base**: sin modelos ni migraciones nuevas. F8 añade estado de operación en archivos y carpetas fuera del repositorio.

## Archivos de estado (`ERP_ESTADO_DIR`)

| Archivo | Lo escribe | Contenido | Aviso en el Inicio del Administrador (FR-017) |
|---|---|---|---|
| `worker.latido` | El worker, en cada vuelta de `procesar_documentos` | Vacío; vale su fecha de modificación | Si su fecha tiene más de 10 minutos: «El procesamiento de documentos no está activo. Avise al encargado de sistemas.» |
| `respaldo.ok` | `respaldar.ps1`, al terminar bien | Fecha y hora ISO del respaldo | Si no existe o tiene más de 26 horas: «El respaldo de anoche no se completó. Avise al encargado de sistemas.» |
| `certificado.vence` | `verificar.ps1`, cada 5 minutos | Fecha ISO de vencimiento del certificado HTTPS | Si faltan 30 días o menos: «El certificado de seguridad vence el DD/MM/AAAA. Avise al encargado de sistemas.» |

Reglas:

- Sin `ERP_ESTADO_DIR` (desarrollo y CI) no hay avisos.
- Un archivo ilegible cuenta como ausente: se avisa, sin detalles técnicos.
- Los textos no llevan rutas, comandos ni nombres técnicos (principio VIII).

## Carpetas del servidor

| Carpeta | Contenido | ACL |
|---|---|---|
| `C:\ConfrontadorNotarial\versiones\<tag>` | Código de una versión y su `.venv` | Lectura: cuenta de servicio; escritura: Administradores |
| `C:\ConfrontadorNotarial\actual` | Enlace a la versión activa | Igual |
| `C:\ConfrontadorNotarial\staticfiles` | `collectstatic` (sin `--clear`), servido por IIS, y `marca\logo.png`, compartido entre versiones | Lectura: IIS |
| `C:\ConfrontadorNotarial\registros` | Registros rotados (5 MB × 10) | Escritura: cuenta de servicio |
| `C:\ConfrontadorNotarial\estado` | Archivos de estado | Escritura: cuenta de servicio |
| `C:\ProgramData\ConfrontadorNotarial\erp.env` | Configuración y claves | Lectura: cuenta de servicio y Administradores |
| `EXPEDIENTES_TEMP_DIR`, `EXPEDIENTES_ORIGINALES_DIR` | Temporales y originales (sin cambios) | Escritura: cuenta de servicio |
| `<disco de respaldos>\ConfrontadorNotarial` | `.bak` diarios y copias de originales, 30 días | Administradores, cuenta de servicio y cuenta de SQL Server |
