# Quickstart · F8 Despliegue en el servidor de la notaría

Guía de instalación, operación y validación. La ejecuta el desarrollador por el acceso remoto que habilita la notaría. Solo datos ficticios en las pruebas.

## 1. Requisitos (los aporta la notaría)

| Requisito | Detalle |
|---|---|
| Servidor | SQLSERVER (Windows Server 2019), con SQL Server 2016 y la base del ERP creada (`specs/045-sql-server/quickstart.md` §4) |
| Acceso remoto | VPN o escritorio remoto detrás de VPN, con una cuenta nominal del desarrollador con permisos de administrador local |
| Nombre interno | Registro DNS, por ejemplo `erp.notaria.local` → IP del servidor |
| Certificado | Emitido por la CA del dominio para ese nombre, instalado en el almacén del equipo |
| Disco de respaldos | Otro disco del servidor, con espacio para 30 días |
| Cuenta de servicio | Cuenta de dominio o local, por ejemplo `svc-confrontador`, sin privilegios de administrador |
| Tope de memoria de SQL Server | Lo fija su administrador, dejando al menos 6 GB libres para Windows y el ERP. `verificar.ps1` avisa si no está fijado |

### Límites de recursos del ERP (FR-013)

| Componente | Límite |
|---|---|
| Web | 1 proceso (`processesPerApplication=1`) con 8 hilos; unos 300 MB |
| Worker | 1 proceso, un documento a la vez; hasta ~1,5 GB durante el OCR |
| Capa de sentido (si se activa) | 3 de los 6 núcleos (`SENTIDO_HILOS=3`) y unos 2,2 GB (F61) |
| Disco | `verificar.ps1` avisa por debajo del 10 % libre en los discos del ERP y de los respaldos |

## 2. Componentes de Windows y software

1. Rol IIS con los módulos **URL Rewrite** y **HttpPlatformHandler** (instaladores oficiales de Microsoft).
2. Python 3.13 de 64 bits, para todos los usuarios.
3. Microsoft ODBC Driver 18 y `sqlcmd`.
4. LibreOffice (MSI oficial), con `C:\Program Files\LibreOffice\program` en el PATH del sistema.
5. Git, si el servidor alcanza GitHub; si no, el paquete de la versión (research R9).

## 3. Instalación

```powershell
# Como administrador, desde la copia del repositorio en el tag elegido:
.\scripts\windows\instalar.ps1 -Version v1.0.0
```

1. Completar `C:\ProgramData\ConfrontadorNotarial\erp.env` desde la plantilla ([contrato](contracts/servidor.md)).
2. Aprovisionar OCR y diccionario como la cuenta de servicio (paso «Verify public test resources» del CI, ejecutado con `runas /user:svc-confrontador`).
3. Enlazar el certificado al sitio de IIS (puerto 443) y poner su huella en `IIS_CERTIFICADO`.
4. Copiar el logo de la notaría (PNG o JPEG) a `C:\ConfrontadorNotarial\staticfiles\marca\logo.png`. Es compartido entre versiones, así que no se pierde al actualizar.
5. `iniciar.ps1 -Rol tarea -Comando migrate`, y después `bootstrap_admin`.
6. `verificar.ps1`: todo en verde.

## 4. Escenarios de validación

| # | Acción | Resultado esperado | Cubre |
|---|---|---|---|
| 1 | Desde 2 PC de la LAN, abrir `http://erp.notaria.local` | Redirige a HTTPS sin avisos; se ingresa y se confronta un kardex ficticio | US1, SC-001 |
| 2 | Desde una red fuera de la LAN | No responde | US1, SR-002 |
| 3 | Reiniciar el servidor | En menos de 5 min el ERP responde y procesa | US2, SC-002 |
| 4 | Terminar a la fuerza el proceso del worker | Vuelve en menos de 2 min y procesa los pendientes | US2, SC-003 |
| 5 | Siete días de operación | Siete `.bak` y siete copias de originales; nada de más de 30 días | US3, SC-004 |
| 6 | `restaurar.ps1 -Fecha <ayer> -Prueba` | Base de prueba restaurada; huellas de los originales iguales; menos de 1 h | US3, SC-004 |
| 7 | `actualizar.ps1 -Version <nueva>` y después `-VolverA <anterior>`; mientras tanto, abrir el ERP desde una PC | Cada paso en menos de 15 min, sin pérdida de datos; mientras la web está detenida, la PC ve la página de mantenimiento en español | US4, SC-005, UX |
| 8 | Cortar la sesión remota a mitad de `actualizar.ps1` y reiniciar | El ERP arranca en una versión completa | US4 |
| 9 | Un día sin salida a internet, confrontando `.docx`, `.doc`, PDF escaneado e imagen | Todo se procesa; ninguna conexión saliente del ERP en el firewall | US5, SC-007 |
| 10 | Detener el worker 11 min; borrar `respaldo.ok`; usar un certificado de prueba que venza en 20 días | Los tres avisos aparecen en el Inicio del Administrador y en el Visor de eventos en menos de 15 min, y desaparecen al corregir | FR-017, SC-008 |
| 11 | 10 sesiones a la vez navegando y subiendo | Las pantallas habituales responden en menos de 2 s | SC-006 |
| 12 | Revisar `registros` tras una semana | Archivos rotados (5 MB × 10) y sin DNI, nombres ni texto | US6, FR-012 |
| 13 | `verificar.ps1` con SQL Server sin tope de memoria, y con el umbral de disco subido temporalmente por encima del espacio libre real | Un aviso por cada caso en el Visor de eventos y en el resumen | FR-013, edge case de disco |

## 5. Operación

- **Comprobar el estado**: `verificar.ps1`.
- **Actualizar**: `actualizar.ps1 -Version <tag>`, fuera del horario de atención.
- **Volver atrás**: `actualizar.ps1 -VolverA <tag>`.
- **Restaurar un día**: `restaurar.ps1 -Fecha AAAAMMDD`. Detiene el ERP mientras restaura.
- **Renovar el certificado**: emitir uno nuevo en la CA del dominio, enlazarlo en IIS y actualizar `IIS_CERTIFICADO`.
