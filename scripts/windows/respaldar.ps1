<#
.SYNOPSIS
F8 · Respaldo diario de la base del ERP y de los borradores originales (FR-007).

.DESCRIPTION
Lo ejecuta la tarea «Confrontador - diario» a las 02:00 con la cuenta de servicio,
y actualizar.ps1 antes de migrar. Guarda en RESPALDO_DIR (otro disco del
servidor), conserva $Dias días, escribe estado\respaldo.ok si todo salió bien y
registra el resultado en el Visor de eventos.
Contrato: specs/046-despliegue/contracts/servidor.md (research R5)
#>
param([int]$Dias = 30)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'comun.ps1')
Import-ErpEntorno

try {
    $fecha = Get-Date -Format 'yyyyMMdd'
    New-Item -ItemType Directory -Force -Path $env:RESPALDO_DIR | Out-Null

    $bak = Join-Path $env:RESPALDO_DIR "confrontador-$fecha.bak"
    Invoke-ErpSql -Consulta "BACKUP DATABASE [$env:DB_NAME] TO DISK = N'$bak' WITH CHECKSUM, INIT" | Out-Null

    $copia = Join-Path $env:RESPALDO_DIR "originales-$fecha"
    & robocopy $env:EXPEDIENTES_ORIGINALES_DIR $copia /MIR /R:2 /W:5 /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy terminó con código $LASTEXITCODE." }

    # Retención: se borra lo que tenga más de $Dias días según la fecha del nombre.
    $limite = (Get-Date).Date.AddDays(-$Dias)
    Get-ChildItem -LiteralPath $env:RESPALDO_DIR |
        Where-Object { $_.Name -match '^(confrontador|originales)-(\d{8})' -and [datetime]::ParseExact($Matches[2], 'yyyyMMdd', $null) -lt $limite } |
        Remove-Item -Recurse -Force

    Set-Content -LiteralPath (Join-Path $env:ERP_ESTADO_DIR 'respaldo.ok') -Value (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz') -Encoding ASCII
    Write-ErpEvento -Mensaje "Respaldo diario completado: $bak" -Tipo Information -Id 1100
} catch {
    Write-ErpEvento -Mensaje "El respaldo diario falló: $($_.Exception.Message)" -Tipo Error -Id 1101
    exit 1
}
