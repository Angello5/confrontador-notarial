<#
.SYNOPSIS
F8 · Actualiza el ERP a una versión nueva, o vuelve a la anterior (FR-010).

.DESCRIPTION
Lo ejecuta el desarrollador, como administrador, por el acceso remoto.
-Version prepara versiones\<Version> sin tocar la que está en uso, respalda,
detiene el ERP (página de mantenimiento), migra, cambia el enlace «actual» al
final y arranca. Si la sesión se corta antes del cambio de enlace, el servidor
sigue en la versión anterior; después, ya está en la nueva completa.
-VolverA restaura el respaldo tomado antes de la última actualización y vuelve
a enlazar esa versión.
-Origen es una carpeta con el código del tag (git clone --branch <tag>, o el
paquete copiado por la sesión remota); -Wheels, la carpeta de wheels si el
servidor no alcanza PyPI.

.EXAMPLE
actualizar.ps1 -Version v1.1.0 -Origen C:\Temp\confrontador-v1.1.0
.EXAMPLE
actualizar.ps1 -VolverA v1.0.0
#>
#Requires -RunAsAdministrator
[CmdletBinding(DefaultParameterSetName = 'Actualizar')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'Actualizar')][string]$Version,
    [Parameter(Mandatory = $true, ParameterSetName = 'Actualizar')][string]$Origen,
    [Parameter(ParameterSetName = 'Actualizar')][string]$Wheels,
    [Parameter(Mandatory = $true, ParameterSetName = 'Volver')][string]$VolverA
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'comun.ps1')
Import-ErpEntorno
$estado = Join-Path $ErpRaiz 'estado'

if ($PSCmdlet.ParameterSetName -eq 'Volver') {
    $respaldo = Get-Content -LiteralPath (Join-Path $estado 'respaldo.previo') -ErrorAction Stop
    Stop-Erp
    Restore-ErpBase -Respaldo $respaldo
    Set-ErpVersionActiva -Version $VolverA
    Start-Erp
    Write-ErpEvento -Mensaje "Se volvió a la versión $VolverA con el respaldo $respaldo." -Tipo Warning -Id 1201
    & (Join-Path $ErpRaiz 'actual\scripts\windows\verificar.ps1')
    exit $LASTEXITCODE
}

$anterior = Get-ErpVersionActiva
New-ErpVersion -Version $Version -Origen $Origen -Wheels $Wheels

# Respaldo antes de migrar: si falla, no se toca nada.
& (Join-Path $PSScriptRoot 'respaldar.ps1')
if ($LASTEXITCODE -ne 0) { throw 'El respaldo previo falló; la actualización se canceló sin cambios.' }
Set-Content -LiteralPath (Join-Path $estado 'respaldo.previo') -Value (Join-Path $env:RESPALDO_DIR "confrontador-$(Get-Date -Format 'yyyyMMdd').bak") -Encoding UTF8

Stop-Erp
$python = Join-Path $ErpRaiz "versiones\$Version\.venv\Scripts\python.exe"
Push-Location -LiteralPath (Join-Path $ErpRaiz "versiones\$Version")
try {
    & $python manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) {
        throw "Las migraciones fallaron. El ERP queda detenido en mantenimiento: ejecute actualizar.ps1 -VolverA $anterior."
    }
} finally { Pop-Location }

Set-ErpVersionActiva -Version $Version
Start-Erp
Write-ErpEvento -Mensaje "ERP actualizado de $anterior a $Version." -Tipo Information -Id 1200
& (Join-Path $ErpRaiz 'actual\scripts\windows\verificar.ps1')
exit $LASTEXITCODE
