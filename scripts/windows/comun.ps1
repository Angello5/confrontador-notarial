# F8 · Funciones comunes de los scripts del servidor. Se cargan con
#   . (Join-Path $PSScriptRoot 'comun.ps1')
# Contrato: specs/046-despliegue/contracts/servidor.md

$ErpRaiz = 'C:\ConfrontadorNotarial'
$ErpEntorno = 'C:\ProgramData\ConfrontadorNotarial\erp.env'
$ErpOrigen = 'ConfrontadorNotarial'
$ErpSitio = 'ConfrontadorNotarial'
$ErpTareaWorker = 'Confrontador - procesamiento'
$ErpTareaDiaria = 'Confrontador - diario'
$ErpTareaVerificacion = 'Confrontador - verificacion'
$ErpMantenimiento = Join-Path $ErpRaiz 'estado\mantenimiento'

function Import-ErpEntorno {
    param([string]$Ruta = $ErpEntorno)
    foreach ($linea in Get-Content -LiteralPath $Ruta -Encoding UTF8) {
        $linea = $linea.Trim()
        if (-not $linea -or $linea.StartsWith('#')) { continue }
        $nombre, $valor = $linea -split '=', 2
        [Environment]::SetEnvironmentVariable($nombre.Trim(), $valor.Trim(), 'Process')
    }
}

function Write-ErpEvento {
    # Solo nombra componentes del sistema: nunca datos personales ni contenido.
    param(
        [Parameter(Mandatory = $true)][string]$Mensaje,
        [ValidateSet('Information', 'Warning', 'Error')][string]$Tipo = 'Warning',
        [int]$Id = 1000
    )
    Write-EventLog -LogName Application -Source $ErpOrigen -EntryType $Tipo -EventId $Id -Message $Mensaje
}

function Invoke-ErpSql {
    # -Integrado usa la cuenta de Windows de quien ejecuta (restauración, como
    # administrador); si no, el login del ERP. La clave viaja en SQLCMDPASSWORD,
    # nunca en la línea de comandos.
    param(
        [Parameter(Mandatory = $true)][string]$Consulta,
        [string]$Base = $env:DB_NAME,
        [switch]$Integrado,
        [string]$Separador = '|'
    )
    $argumentos = @('-S', $env:DB_HOST, '-d', $Base, '-b', '-h', '-1', '-W', '-s', $Separador, '-Q', "SET NOCOUNT ON; $Consulta")
    if ($env:DB_TRUST_SERVER_CERTIFICATE -match '^(1|true|yes)$') { $argumentos += '-C' }
    if ($Integrado) {
        $argumentos += '-E'
    } else {
        $argumentos += @('-U', $env:DB_USER)
        $env:SQLCMDPASSWORD = $env:DB_PASSWORD
    }
    try {
        $salida = & sqlcmd @argumentos
        if ($LASTEXITCODE -ne 0) { throw "sqlcmd terminó con código $LASTEXITCODE." }
        $salida
    } finally {
        Remove-Item Env:\SQLCMDPASSWORD -ErrorAction SilentlyContinue
    }
}

function Stop-Erp {
    # Página de mantenimiento (web.config) y servicios detenidos.
    New-Item -ItemType File -Force -Path $ErpMantenimiento | Out-Null
    Import-Module WebAdministration
    Stop-ScheduledTask -TaskName $ErpTareaWorker -ErrorAction SilentlyContinue
    # Detener la tarea no termina el proceso de Python que lanzó.
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -match 'procesar_documentos' } |
        Invoke-CimMethod -MethodName Terminate | Out-Null
    if ((Get-WebAppPoolState -Name $ErpSitio).Value -ne 'Stopped') { Stop-WebAppPool -Name $ErpSitio }
}

function Start-Erp {
    Import-Module WebAdministration
    Start-WebAppPool -Name $ErpSitio
    Start-ScheduledTask -TaskName $ErpTareaWorker
    Remove-Item -LiteralPath $ErpMantenimiento -ErrorAction SilentlyContinue
}

function Set-ErpVersionActiva {
    param([Parameter(Mandatory = $true)][string]$Version)
    $destino = Join-Path $ErpRaiz "versiones\$Version"
    if (-not (Test-Path -LiteralPath $destino)) { throw "No existe la versión $Version." }
    $actual = Join-Path $ErpRaiz 'actual'
    if (Test-Path -LiteralPath $actual) { cmd /c rmdir "$actual" | Out-Null }
    New-Item -ItemType Junction -Path $actual -Target $destino | Out-Null
}

function Get-ErpVersionActiva {
    $actual = Get-Item -LiteralPath (Join-Path $ErpRaiz 'actual') -ErrorAction SilentlyContinue
    if ($actual -and $actual.Target) { Split-Path -Leaf @($actual.Target)[0] }
}

function New-ErpVersion {
    # Prepara versiones\<Version> sin tocar la que está en uso: código, .venv y estáticos.
    param(
        [Parameter(Mandatory = $true)][string]$Version,
        [Parameter(Mandatory = $true)][string]$Origen,
        [string]$Wheels
    )
    $destino = Join-Path $ErpRaiz "versiones\$Version"
    if (Test-Path -LiteralPath $destino) { throw "La versión $Version ya está preparada." }
    & robocopy $Origen $destino /E /XD .git .venv __pycache__ staticfiles node_modules /XF *.pyc /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy terminó con código $LASTEXITCODE." }
    Copy-Item -LiteralPath (Join-Path $destino 'scripts\windows\web.config') -Destination (Join-Path $destino 'web.config')
    & py -3.13 -m venv (Join-Path $destino '.venv')
    $python = Join-Path $destino '.venv\Scripts\python.exe'
    $pip = @('-m', 'pip', 'install', '--require-hashes', '--only-binary', ':all:', '--no-binary', 'antlr4-python3-runtime', '-r', (Join-Path $destino 'requirements.txt'))
    if ($Wheels) { $pip += @('--no-index', '--find-links', $Wheels) }
    & $python @pip
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
    Push-Location -LiteralPath $destino
    try {
        & $python manage.py collectstatic --noinput
        if ($LASTEXITCODE -ne 0) { throw 'collectstatic falló.' }
    } finally { Pop-Location }
}

function Restore-ErpBase {
    # Restaura la base del ERP desde un .bak (requiere permisos de administrador de SQL Server).
    param([Parameter(Mandatory = $true)][string]$Respaldo)
    $base = $env:DB_NAME
    try {
        Invoke-ErpSql -Integrado -Base master -Consulta "ALTER DATABASE [$base] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; RESTORE DATABASE [$base] FROM DISK = N'$Respaldo' WITH REPLACE, CHECKSUM;" | Out-Null
    } finally {
        # Si el RESTORE falla, la base no debe quedar con un solo usuario.
        Invoke-ErpSql -Integrado -Base master -Consulta "ALTER DATABASE [$base] SET MULTI_USER;" | Out-Null
    }
}
