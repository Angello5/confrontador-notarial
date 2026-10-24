# Research: F8 · Despliegue en el servidor de la notaría

No quedan `[NEEDS CLARIFICATION]` en la spec. Las decisiones salen del código del ERP y de la plataforma Windows Server 2019 (IIS, Programador de tareas, Visor de eventos), sin componentes ajenos a Microsoft salvo un servidor WSGI.

## R1. Servidor web y HTTPS (FR-002, SR-001, SR-006)

- **Decision**: IIS, el rol web de Windows Server.
  - Un sitio con enlace HTTPS en el puerto 443, con el certificado que emite la CA del dominio para el nombre interno.
  - Una regla de redirección HTTP→HTTPS en el puerto 80 (módulo URL Rewrite).
  - IIS sirve `/static/` desde `STATIC_ROOT`.
  - El resto lo pasa a la aplicación con **HttpPlatformHandler**.
- **Rationale**:
  - Microsoft recomienda HttpPlatformHandler para Python en IIS; wfastcgi ya no se mantiene ([Configure Python web apps for IIS](https://learn.microsoft.com/en-us/visualstudio/python/configure-web-apps-for-iis-windows?view=visualstudio)).
  - IIS gestiona el certificado del dominio con las herramientas que el equipo de sistemas ya conoce.
  - HttpPlatformHandler arranca el proceso de Python, lo reinicia si muere y lo vuelve a levantar al reciclar.
- **Alternatives considered**:
  - wfastcgi (sin mantenimiento);
  - el servidor WSGI expuesto directo (no maneja el certificado del dominio ni la redirección);
  - Caddy o nginx para Windows (otro componente que el equipo de sistemas no conoce).

## R2. Servidor WSGI (FR-004)

- **Decision**: `waitress` 3.0.2, la única dependencia nueva. Escucha solo en `127.0.0.1`, en el puerto que asigna HttpPlatformHandler (`HTTP_PLATFORM_PORT`), con `url_scheme=https`.
- **Rationale**:
  - `runserver` es solo para desarrollo, y en las dependencias del ERP no hay ningún servidor WSGI.
  - `waitress` es Python puro, funciona en Windows y no arrastra dependencias.
  - Solo IIS habla con él, por localhost, y la conexión de la usuaria ya llegó por HTTPS. Declarar `https` hace que Django vea la petición como segura: la cookie `Secure` y la comprobación de origen CSRF funcionan sin `CSRF_TRUSTED_ORIGINS` ni cabeceras de proxy.
- **Alternatives considered**:
  - gunicorn (no corre en Windows);
  - uvicorn con ASGI (el ERP es WSGI; añade dependencias);
  - `SECURE_PROXY_SSL_HEADER` (IIS no envía `X-Forwarded-Proto` sin configurar variables de servidor).

## R3. Procesamiento y tareas periódicas (FR-004, FR-009, FR-017)

- **Decision**: el **Programador de tareas de Windows** con la cuenta de servicio, en «ejecutar tanto si el usuario inició sesión como si no».
  - **Worker**: `procesar_documentos --continuo` al iniciar el sistema. Se reinicia cada minuto ante un fallo (hasta 999 veces) y no tiene límite de duración.
  - **Diario, 02:00**: `limpiar_temporales` y el respaldo (R5).
  - **Cada 5 minutos**: la verificación (R7).
- **Rationale**:
  - Viene con Windows: no hay que instalar NSSM ni WinSW, ni escribir servicios con `pywin32`.
  - El worker ya sobrevive a cortes de la base (F63).
  - **Hallado al implementar**: el «reiniciar si falla» del Programador de tareas solo actúa si la tarea no logra arrancar, no cuando el proceso sale con error. Por eso `iniciar.ps1 -Rol worker` relanza Python en un bucle, con 30 s de pausa y un aviso en el Visor de eventos (SC-003). Y `Stop-Erp` termina el proceso de Python, porque detener la tarea no lo hace.
- **Alternatives considered**:
  - NSSM o WinSW (binarios de terceros);
  - `pywin32` (código de servicio propio);
  - el worker dentro de IIS (IIS recicla procesos, y el worker no atiende peticiones).

## R4. Configuración y secretos (FR-011, FR-014, SR-003, SR-004)

- **Decision**: el archivo `C:\ProgramData\ConfrontadorNotarial\erp.env` contiene las variables de hoy: `DJANGO_SECRET_KEY`, `DB_*`, `DJANGO_ALLOWED_HOSTS`, `ERP_NOMBRE`, `ERP_LOGO`, `EXPEDIENTES_*` y `SENTIDO_*`, más dos nuevas: `ERP_REGISTROS_DIR` y `ERP_ESTADO_DIR`. Su ACL da lectura solo a la cuenta de servicio y a Administradores.
  - Un único lanzador, `scripts/windows/iniciar.ps1 -Rol web|worker|tarea`, lee el archivo, define las variables en su propio proceso y arranca Python.
  - IIS (HttpPlatformHandler) y el Programador de tareas llaman a ese lanzador.
  - Ninguna clave pasa por `web.config`, por la línea de comandos ni por variables de máquina.
- **Rationale**: SR-004 prohíbe claves en la línea de comandos. Las variables de máquina las lee cualquier proceso, y `web.config` vive en la carpeta de la aplicación.
- **Alternatives considered**:
  - variables de entorno de máquina (las lee cualquier usuario);
  - `environmentVariables` en `web.config` (la clave quedaría junto al código);
  - un paquete `python-dotenv` (una dependencia para lo que hacen diez líneas de PowerShell).

## R5. Respaldo y restauración (FR-007, FR-008, SR-005)

- **Decision**: `scripts/windows/respaldar.ps1` corre cada día a las 02:00 con la cuenta de servicio.
  - Ejecuta `BACKUP DATABASE confrontador TO DISK = '<RESPALDO_DIR>\confrontador-AAAAMMDD.bak' WITH CHECKSUM, INIT` con `sqlcmd` y el login del ERP; `db_owner` incluye el permiso de respaldo.
  - Copia los originales con `robocopy /MIR` a `<RESPALDO_DIR>\originales-AAAAMMDD`.
  - Borra lo que tenga más de 30 días.
  - Si todo sale bien, escribe `respaldo.ok` en `ERP_ESTADO_DIR`. Si algo falla, registra un error en el Visor de eventos.
  - `RESPALDO_DIR` está en otro disco y su ACL da acceso solo a Administradores, a la cuenta de servicio y a la cuenta del servicio de SQL Server, que es quien escribe el `.bak`.
- **Restauración**: `scripts/windows/restaurar.ps1 -Fecha AAAAMMDD` detiene la web y el worker, ejecuta `RESTORE DATABASE ... WITH REPLACE`, restaura los originales y reinicia. Con `-Prueba`, restaura en la base `confrontador_prueba_restauracion` y compara las huellas SHA-256 de los originales sin tocar producción (FR-008, SC-004).
- **Rationale**: funciona con cualquier edición; Express no tiene SQL Server Agent. Si la notaría tiene un plan de mantenimiento de SQL Server, su administrador añade la base `confrontador`.
- **Alternatives considered**:
  - planes de mantenimiento de SQL Server Agent (no existen en Express; edición por confirmar);
  - Windows Server Backup del volumen entero (copia más de lo necesario y no permite restaurar solo el ERP).

## R6. Recursos sin internet (FR-006)

- **Decision**:
  - **OCR y diccionario**: los modelos y el diccionario `es_PE` se aprovisionan con el mismo paso verificado del CI, ejecutado como la cuenta de servicio. Así quedan en su `%USERPROFILE%\.cache\notaria-ocr`, que es donde los busca el código (`Path.home()`), sin tocar el código.
  - **LibreOffice**: se instala con su MSI oficial y `C:\Program Files\LibreOffice\program` se añade al PATH del sistema, porque el código llama a `soffice`.
  - **Capa de sentido**: queda apagada (`SENTIDO_ACTIVO` vacío).
- **Rationale**: el código ya funciona así; IIS carga el perfil de la cuenta con `loadUserProfile=true` en el grupo de aplicaciones.
- **Alternatives considered**: hacer configurables las rutas de caché (no hace falta si se aprovisiona con la cuenta correcta).

## R7. Avisos y verificación (FR-015, FR-017, SC-008)

- **Decision**: tres archivos de estado en `ERP_ESTADO_DIR`:
  - `worker.latido`: el worker lo toca en cada vuelta;
  - `respaldo.ok`: lo escribe el respaldo correcto;
  - `certificado.vence`: fecha ISO que escribe la verificación desde el certificado enlazado en IIS.
- **Quién los usa**:
  - **Inicio del Administrador**: `expedientes/services.py::avisos_sistema()` lee los tres archivos y devuelve los avisos que correspondan según los umbrales de FR-017 (26 h, 30 días y 10 min). El Inicio los muestra con el mismo componente que los avisos de documentos ilegibles. Si `ERP_ESTADO_DIR` no está definido, como en desarrollo y en el CI, no hay avisos.
  - **`scripts/windows/verificar.ps1`**: corre cada 5 minutos y como comprobación en un paso (FR-015). Revisa web (HTTPS), worker (latido), base (`manage.py check --database default`), recursos (`verificar_modelos_sentido` si la capa está activa, `soffice --version`), certificado, tope de memoria de SQL Server (FR-013) y espacio libre en los discos del ERP y de los respaldos (por debajo del 10 %). Registra cada problema en el Visor de eventos con el origen `ConfrontadorNotarial`. Sin argumentos, también imprime el resumen.
- **Rationale**: los archivos no necesitan migraciones ni tablas nuevas, y los escriben procesos que ya existen. El umbral de 10 minutos deja margen: el worker da una vuelta cada 2 segundos y un OCR largo no pasa de unos minutos.
- **Alternatives considered**: una tabla de estado (migración y escrituras desde PowerShell a SQL Server); correo (no hay servidor de correo acordado).

## R8. Registros (FR-012)

- **Decision**:
  - `LOGGING` en `config/settings.py`: un `RotatingFileHandler` de 5 MB × 10 archivos en `ERP_REGISTROS_DIR`, solo si está definido; sin él, consola, como hoy.
  - Mismo formato para la web y el worker.
  - Los mensajes actuales ya no llevan datos personales (principio IV), y no se añaden mensajes con contenido.
  - HttpPlatformHandler deja `stdoutLogEnabled=false`.
- **Rationale**: la biblioteca estándar resuelve la rotación.
- **Alternatives considered**: los registros de stdout de HttpPlatformHandler (sin rotación).

## R9. Instalación, actualización y vuelta atrás (FR-010, US4)

- **Decision**: estructura en `C:\ConfrontadorNotarial\`:
  - `versiones\<tag>\`: copia del repositorio en ese tag, con su `.venv` propio;
  - `actual`: enlace de directorio (junction) a la versión activa; IIS y las tareas apuntan a `actual`;
  - `staticfiles`, `registros` y `estado`: compartidos entre versiones.
- **`scripts/windows/actualizar.ps1 -Version <tag>`** sigue este orden:
  1. prepara `versiones\<tag>`: código, `.venv` con `--require-hashes` y `collectstatic`, sin tocar lo que está en uso;
  2. ejecuta el respaldo (R5);
  3. detiene la web y el worker;
  4. aplica las migraciones;
  5. cambia `actual` al final;
  6. arranca y verifica (R7).
- **`-VolverA <tag>`**: restaura el respaldo previo a la actualización y vuelve a enlazar la versión anterior.
- **Si la sesión remota se corta a mitad**: el enlace solo cambió si todo lo anterior terminó, así que el servidor arranca en la versión anterior o en la nueva completa (US4, escenario 4).
- **Rationale**: cambiar un enlace es casi instantáneo, y el respaldo previo a las migraciones hace reversible la base.
- **Alternatives considered**:
  - `git pull` sobre la carpeta en uso (puede quedar a medias);
  - revertir migraciones (no todas son reversibles).
- **Supuesto**: durante el mantenimiento, el servidor alcanza GitHub y PyPI. Si no, el desarrollador lleva un paquete con el código del tag y los wheels (`pip download --require-hashes`) por la sesión remota. La guía cubre los dos casos.

## R10. Red y recursos (SR-002, FR-013, SC-006)

- **Decision**:
  - **Firewall**: una regla de entrada para TCP 443 y 80 limitada a `LocalSubnet`; no se toca el puerto de SQL Server.
  - **Web**: waitress con 8 hilos y una sola instancia; HttpPlatformHandler con `processesPerApplication=1`, para que solo haya un proceso de la web.
  - **Worker**: uno solo, como hoy.
  - **SQL Server**: el tope de memoria lo fija su administrador (F61).
- **Rationale**: 10 usuarias no necesitan más; un solo proceso web hace que la caché por proceso (`version_estaticos`) sea coherente.

## R11. Diagrama de arquitectura (FR-016)

- **Decision**: la vista de despliegue de `docs/arquitectura/erp-notarial-c4.drawio` pasa a mostrar SQLSERVER con IIS, la web (waitress), el worker (Programador de tareas) y SQL Server en la misma máquina, y la LAN con las PC. Se quitan la VM Ubuntu, Hyper-V y Docker Compose.
