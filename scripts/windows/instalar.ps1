<#
.SYNOPSIS
F8 · Instala el ERP en el servidor de la notaría (Windows nativo).

.DESCRIPTION
Se ejecuta una vez, como administrador, desde una copia del repositorio en el
tag que se instala. La primera ejecución crea erp.env desde la plantilla y se
detiene para completarlo; la segunda instala:
  1. Carpetas con sus ACL (specs/046-despliegue/data-model.md).
  2. Origen «ConfrontadorNotarial» en el Visor de eventos.
  3. La versión inicial en versiones\<Version> y el enlace «actual».
  4. Grupo de aplicaciones y sitio de IIS (HTTPS 443 + HTTP 80, /static/).
  5. Regla de firewall solo para la red local.
  6. Tareas programadas: procesamiento, diario (limpieza + respaldo) y verificación.
La clave de la cuenta de servicio se pide por pantalla; nunca se guarda.
Guía: specs/046-despliegue/quickstart.md

.EXAMPLE
instalar.ps1 -Version v1.0.0 -CuentaServicio NOTARIA\svc-confrontador -Certificado 0123ABCD...
#>
#Requires -RunAsAdministrator
param(
    [Parameter(Mandatory = $true)][string]$Version,
    [Parameter(Mandatory = $true)][string]$CuentaServicio,
    [string]$Certificado,
    [string]$Wheels
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'comun.ps1')
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# erp.env: solo la cuenta de servicio, SYSTEM y Administradores lo leen.
$carpetaEntorno = Split-Path -Parent $ErpEntorno
New-Item -ItemType Directory -Force -Path $carpetaEntorno | Out-Null
if (-not (Test-Path -LiteralPath $ErpEntorno)) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'erp.env.ejemplo') -Destination $ErpEntorno
    & icacls $ErpEntorno /inheritance:r /grant:r '*S-1-5-32-544:F' '*S-1-5-18:F' "${CuentaServicio}:R" | Out-Null
    Write-Output "Complete $ErpEntorno y vuelva a ejecutar instalar.ps1."
    exit 0
}
Import-ErpEntorno

# 1. Carpetas y permisos.
foreach ($nombre in 'versiones', 'staticfiles\marca', 'registros', 'estado') {
    New-Item -ItemType Directory -Force -Path (Join-Path $ErpRaiz $nombre) | Out-Null
}
foreach ($ruta in $env:EXPEDIENTES_TEMP_DIR, $env:EXPEDIENTES_ORIGINALES_DIR, $env:RESPALDO_DIR) {
    New-Item -ItemType Directory -Force -Path $ruta | Out-Null
}
& icacls (Join-Path $ErpRaiz 'versiones') /grant "${CuentaServicio}:(OI)(CI)RX" | Out-Null
& icacls (Join-Path $ErpRaiz 'staticfiles') /grant '*S-1-5-32-568:(OI)(CI)RX' "${CuentaServicio}:(OI)(CI)RX" | Out-Null
foreach ($ruta in (Join-Path $ErpRaiz 'registros'), (Join-Path $ErpRaiz 'estado'), $env:EXPEDIENTES_TEMP_DIR, $env:EXPEDIENTES_ORIGINALES_DIR) {
    & icacls $ruta /grant "${CuentaServicio}:(OI)(CI)M" | Out-Null
}
# Respaldos: datos personales (SR-005). El .bak lo escribe el servicio de SQL Server.
& icacls $env:RESPALDO_DIR /inheritance:r /grant:r '*S-1-5-32-544:(OI)(CI)F' '*S-1-5-18:(OI)(CI)F' "${CuentaServicio}:(OI)(CI)M" 'NT SERVICE\MSSQLSERVER:(OI)(CI)M' | Out-Null

# 2. Visor de eventos.
if (-not [System.Diagnostics.EventLog]::SourceExists($ErpOrigen)) {
    New-EventLog -LogName Application -Source $ErpOrigen
}

# 3. Versión inicial.
New-ErpVersion -Version $Version -Origen $repo -Wheels $Wheels
Set-ErpVersionActiva -Version $Version

# 4. IIS: grupo de aplicaciones con la cuenta de servicio y su perfil cargado
#    (los modelos de OCR viven en su %USERPROFILE%), sin código administrado.
$credencial = Get-Credential -UserName $CuentaServicio -Message 'Clave de la cuenta de servicio del ERP'
$clave = $credencial.GetNetworkCredential().Password
Import-Module WebAdministration
$grupo = "IIS:\AppPools\$ErpSitio"
if (-not (Test-Path $grupo)) { New-WebAppPool -Name $ErpSitio | Out-Null }
Set-ItemProperty $grupo -Name managedRuntimeVersion -Value ''
Set-ItemProperty $grupo -Name startMode -Value 'AlwaysRunning'
Set-ItemProperty $grupo -Name processModel -Value @{ userName = $CuentaServicio; password = $clave; identityType = 3; loadUserProfile = $true }
$nombre = ($env:DJANGO_ALLOWED_HOSTS -split ',')[0].Trim()
if (-not (Get-Website -Name $ErpSitio)) {
    New-Website -Name $ErpSitio -PhysicalPath (Join-Path $ErpRaiz 'actual') -ApplicationPool $ErpSitio -Port 80 -HostHeader $nombre | Out-Null
    New-WebBinding -Name $ErpSitio -Protocol https -Port 443 -HostHeader $nombre -SslFlags 1
    New-WebVirtualDirectory -Site $ErpSitio -Name static -PhysicalPath (Join-Path $ErpRaiz 'staticfiles') | Out-Null
}
if ($Certificado) {
    (Get-WebBinding -Name $ErpSitio -Protocol https).AddSslCertificate($Certificado, 'my')
}

# 5. Firewall: solo la red local, solo HTTP y HTTPS (SR-002).
$regla = 'Confrontador Notarial (HTTP/HTTPS)'
if (-not (Get-NetFirewallRule -DisplayName $regla -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $regla -Direction Inbound -Protocol TCP -LocalPort 80, 443 -RemoteAddress LocalSubnet -Action Allow | Out-Null
}

# 6. Tareas programadas con la cuenta de servicio, sin sesión iniciada.
$powershell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$scripts = Join-Path $ErpRaiz 'actual\scripts\windows'
function Accion([string]$Argumentos) {
    New-ScheduledTaskAction -Execute $powershell -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass $Argumentos"
}
function Registrar([string]$Nombre, $Acciones, $Disparadores, $Ajustes) {
    Register-ScheduledTask -TaskName $Nombre -Action $Acciones -Trigger $Disparadores -Settings $Ajustes -User $CuentaServicio -Password $clave -RunLevel Limited -Force | Out-Null
}
Registrar $ErpTareaWorker (Accion "-File `"$scripts\iniciar.ps1`" -Rol worker") (New-ScheduledTaskTrigger -AtStartup) (
    New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -StartWhenAvailable)
Registrar $ErpTareaDiaria @(
    (Accion "-File `"$scripts\iniciar.ps1`" -Rol tarea -Comando limpiar_temporales"),
    (Accion "-File `"$scripts\respaldar.ps1`"")
) (New-ScheduledTaskTrigger -Daily -At '02:00') (
    New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 10) -StartWhenAvailable)
Registrar $ErpTareaVerificacion (Accion "-File `"$scripts\verificar.ps1`"") @(
    (New-ScheduledTaskTrigger -AtStartup),
    (New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5))
) (New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 4))
Start-ScheduledTask -TaskName $ErpTareaWorker

Write-Output @"
Instalada la versión $Version. Pasos siguientes (specs/046-despliegue/quickstart.md §3):
  - Aprovisionar OCR y diccionario como $CuentaServicio.
  - Copiar el logo a $ErpRaiz\staticfiles\marca\logo.png.
  - iniciar.ps1 -Rol tarea -Comando migrate, y luego bootstrap_admin.
  - verificar.ps1
"@
