<#
.SYNOPSIS
F8 · Lanzador del ERP: carga erp.env y arranca la web, el worker o un comando.

.DESCRIPTION
Lo llaman IIS (HttpPlatformHandler, -Rol web) y el Programador de tareas
(-Rol worker, -Rol tarea). Las claves solo viven en erp.env, protegido por ACL;
nunca pasan por la línea de comandos ni por web.config.
Contrato: specs/046-despliegue/contracts/servidor.md

.EXAMPLE
iniciar.ps1 -Rol tarea -Comando "check --database default"
#>
param(
    [Parameter(Mandatory = $true)][ValidateSet('web', 'worker', 'tarea')][string]$Rol,
    [string]$Comando
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'comun.ps1')
Import-ErpEntorno
# Un archivo de registro por rol (config/settings.py, LOGGING).
$env:ERP_ROL = if ($Rol -eq 'tarea') { 'tarea-' + ($Comando -split ' ')[0] } else { $Rol }
$env:PYTHONUTF8 = '1'

# scripts\windows → raíz de la versión (C:\ConfrontadorNotarial\actual).
$app = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location -LiteralPath $app
$python = Join-Path $app '.venv\Scripts\python.exe'

switch ($Rol) {
    'web' {
        # Solo IIS habla con waitress, por localhost, y la conexión ya llegó por HTTPS.
        & $python -m waitress "--listen=127.0.0.1:$env:HTTP_PLATFORM_PORT" --url-scheme=https --threads=8 config.wsgi:application
    }
    'worker' {
        # El Programador de tareas no reinicia una tarea cuyo proceso termina con
        # error: se vuelve a lanzar aquí, con una pausa para no girar en vacío (SC-003).
        while ($true) {
            & $python -u manage.py procesar_documentos --continuo
            Write-ErpEvento -Mensaje "El procesamiento de documentos se detuvo (código $LASTEXITCODE); se reinicia en 30 segundos." -Id 1001
            Start-Sleep -Seconds 30
        }
    }
    'tarea' {
        if (-not $Comando) { throw 'Falta -Comando para -Rol tarea.' }
        & $python manage.py @($Comando -split ' ')
    }
}
exit $LASTEXITCODE
