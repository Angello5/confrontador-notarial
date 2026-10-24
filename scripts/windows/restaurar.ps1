<#
.SYNOPSIS
F8 · Restaura la base del ERP y los originales de un día (FR-008).

.DESCRIPTION
Lo ejecuta el desarrollador o el administrador, como administrador del servidor
y de SQL Server.
- Sin -Prueba: detiene el ERP (página de mantenimiento), restaura la base y los
  originales del día indicado y vuelve a arrancar.
- Con -Prueba: restaura en la base confrontador_prueba_restauracion, comprueba
  que cada borrador original copiado tiene la huella SHA-256 que guarda la base
  y la borra al terminar. No toca producción (SC-004).

.EXAMPLE
restaurar.ps1 -Fecha 20261023 -Prueba
#>
param(
    [Parameter(Mandatory = $true)][ValidatePattern('^\d{8}$')][string]$Fecha,
    [switch]$Prueba
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'comun.ps1')
Import-ErpEntorno

$bak = Join-Path $env:RESPALDO_DIR "confrontador-$Fecha.bak"
$copia = Join-Path $env:RESPALDO_DIR "originales-$Fecha"
if (-not (Test-Path -LiteralPath $bak)) { throw "No hay respaldo de la base del $Fecha." }
if (-not (Test-Path -LiteralPath $copia)) { throw "No hay copia de los originales del $Fecha." }

if (-not $Prueba) {
    Stop-Erp
    try {
        Restore-ErpBase -Respaldo $bak
        & robocopy $copia $env:EXPEDIENTES_ORIGINALES_DIR /MIR /R:2 /W:5 /NFL /NDL /NJH /NJS /NP | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "robocopy terminó con código $LASTEXITCODE." }
    } finally {
        Start-Erp
    }
    Write-ErpEvento -Mensaje "Se restauró el ERP al estado del $Fecha." -Tipo Warning -Id 1300
    Write-Output "ERP restaurado al $Fecha."
    exit 0
}

$prueba = 'confrontador_prueba_restauracion'
$inicio = Get-Date
# Los archivos de datos se restauran con otro nombre para no pisar los de producción.
$datos = (Invoke-ErpSql -Integrado -Base master -Consulta "SELECT CAST(SERVERPROPERTY('InstanceDefaultDataPath') AS nvarchar(260))").Trim()
$mover = foreach ($fila in Invoke-ErpSql -Integrado -Base master -Consulta "RESTORE FILELISTONLY FROM DISK = N'$bak'") {
    $logico, $fisico = ($fila -split '\|')[0, 1]
    "MOVE N'$logico' TO N'$(Join-Path $datos ($prueba + '_' + (Split-Path -Leaf $fisico)))'"
}
Invoke-ErpSql -Integrado -Base master -Consulta "RESTORE DATABASE [$prueba] FROM DISK = N'$bak' WITH $($mover -join ', '), REPLACE, CHECKSUM" | Out-Null
try {
    $huellas = @(Invoke-ErpSql -Integrado -Base $prueba -Consulta "SELECT hash_archivo FROM expedientes_documento WHERE rol = 'BORRADOR'") |
        ForEach-Object { $_.Trim().ToLower() }
    $originales = @(Get-ChildItem -LiteralPath $copia -Recurse -Filter 'original.docx' -File)
    $distintos = @($originales | Where-Object { (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower() -notin $huellas })
    $minutos = [math]::Round(((Get-Date) - $inicio).TotalMinutes, 1)
    Write-Output "Prueba del $Fecha : $($originales.Count) originales, $($distintos.Count) con huella distinta, $minutos min."
    if ($distintos.Count) { exit 1 }
} finally {
    Invoke-ErpSql -Integrado -Base master -Consulta "DROP DATABASE [$prueba]" | Out-Null
}
