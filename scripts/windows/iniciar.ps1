# F8 · Lanzador único del ERP en el servidor (contracts/servidor.md).
# Lee erp.env, define las variables solo en este proceso y arranca Python.
#   -Rol web     lo llama IIS (HttpPlatformHandler), que define HTTP_PLATFORM_PORT
#   -Rol worker  lo llama la tarea «Confrontador · procesamiento»
#   -Rol tarea -Comando <cmd>  ejecuta un comando de manage.py
# Ninguna clave pasa por argumentos ni por variables de máquina.
param(
    [Parameter(Mandatory)][ValidateSet('web', 'worker', 'tarea')][string]$Rol,
    [string]$Comando,
    [string]$Env = 'C:\ProgramData\ConfrontadorNotarial\erp.env'
)
$ErrorActionPreference = 'Stop'

foreach ($linea in Get-Content -LiteralPath $Env -Encoding UTF8) {
    $linea = $linea.Trim()
    if (-not $linea -or $linea.StartsWith('#')) { continue }
    $nombre, $valor = $linea -split '=', 2
    [Environment]::SetEnvironmentVariable($nombre.Trim(), $valor, 'Process')
}
$env:PYTHONIOENCODING = 'utf-8'

$raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$python = Join-Path $raiz '.venv\Scripts\python.exe'
Set-Location -LiteralPath $raiz

switch ($Rol) {
    'web' {
        if (-not $env:HTTP_PLATFORM_PORT) { throw 'Falta HTTP_PLATFORM_PORT (lo define IIS).' }
        # IIS ya recibió la conexión por HTTPS; waitress solo escucha en localhost.
        & $python -m waitress --listen="127.0.0.1:$($env:HTTP_PLATFORM_PORT)" `
            --threads=8 --url-scheme=https config.wsgi:application
    }
    'worker' {
        # El Programador de tareas no reintenta cuando el proceso termina con
        # error (solo si no logra arrancarlo): el lanzador lo vuelve a levantar.
        while ($true) {
            & $python manage.py procesar_documentos --continuo
            Start-Sleep -Seconds 60
        }
    }
    'tarea' {
        if (-not $Comando) { throw 'Falta -Comando.' }
        & $python manage.py $Comando
    }
}
exit $LASTEXITCODE
