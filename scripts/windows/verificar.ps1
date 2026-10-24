<#
.SYNOPSIS
F8 · Comprobación en un paso del ERP en el servidor (FR-015) y avisos (FR-017).

.DESCRIPTION
La ejecuta la tarea «Confrontador - verificacion» cada 5 minutos, y a mano.
Revisa la web, el procesamiento, la base, LibreOffice, la capa de sentido (si
está activa), el certificado HTTPS, el tope de memoria de SQL Server y el
espacio libre en disco. Cada problema queda en el Visor de eventos; además
escribe estado\certificado.vence para el Inicio del Administrador.
La primera petición a la web tras un reinicio también arranca su proceso en IIS.
Termina con código 1 si algo falla.
#>
param([int]$UmbralDisco = 10)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'comun.ps1')
Import-ErpEntorno

$problemas = New-Object System.Collections.Generic.List[string]
function Revisar([string]$Componente, [scriptblock]$Prueba) {
    try {
        $detalle = & $Prueba
        if ($detalle) { $problemas.Add("$Componente : $detalle") }
        else { Write-Output "OK      $Componente" }
    } catch {
        $problemas.Add("$Componente : $($_.Exception.Message)")
    }
}

$nombre = ($env:DJANGO_ALLOWED_HOSTS -split ',')[0].Trim()
Revisar 'Web' {
    $respuesta = Invoke-WebRequest -Uri "https://$nombre/accounts/login/" -UseBasicParsing -TimeoutSec 60
    if ($respuesta.StatusCode -ne 200) { "respondió $($respuesta.StatusCode)" }
}
Revisar 'Procesamiento' {
    $latido = Get-Item -LiteralPath (Join-Path $env:ERP_ESTADO_DIR 'worker.latido') -ErrorAction SilentlyContinue
    if (-not $latido -or ((Get-Date) - $latido.LastWriteTime).TotalMinutes -gt 10) { 'sin actividad hace más de 10 minutos' }
}
Revisar 'Base' {
    & (Join-Path $PSScriptRoot 'iniciar.ps1') -Rol tarea -Comando 'check --database default' | Out-Null
    if ($LASTEXITCODE -ne 0) { 'la verificación de la base falló' }
}
Revisar 'LibreOffice' {
    if (-not (Get-Command soffice -ErrorAction SilentlyContinue)) { 'soffice no está en el PATH del sistema' }
}
if ($env:SENTIDO_ACTIVO -match '^(1|true|yes)$') {
    Revisar 'Capa de sentido' {
        & (Join-Path $PSScriptRoot 'iniciar.ps1') -Rol tarea -Comando 'verificar_modelos_sentido' | Out-Null
        if ($LASTEXITCODE -ne 0) { 'los modelos no coinciden con su manifiesto' }
    }
}
Revisar 'Certificado' {
    $certificado = Get-Item -LiteralPath "Cert:\LocalMachine\My\$env:IIS_CERTIFICADO"
    Set-Content -LiteralPath (Join-Path $env:ERP_ESTADO_DIR 'certificado.vence') -Value $certificado.NotAfter.ToString('yyyy-MM-dd') -Encoding ASCII
    $dias = ($certificado.NotAfter - (Get-Date)).TotalDays
    if ($dias -le 30) { "vence el $($certificado.NotAfter.ToString('dd/MM/yyyy'))" }
}
Revisar 'Memoria de SQL Server' {
    $tope = [long](Invoke-ErpSql -Consulta "SELECT CAST(value_in_use AS bigint) FROM sys.configurations WHERE name = 'max server memory (MB)'").Trim()
    $total = [long]((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1MB)
    if ($tope -ge 2147483647) { 'sin tope de memoria' }
    elseif ($total - $tope -lt 6144) { "el tope deja menos de 6 GB libres ($tope MB de $total MB)" }
}
Revisar 'Disco' {
    $rutas = @($ErpRaiz, $env:EXPEDIENTES_TEMP_DIR, $env:EXPEDIENTES_ORIGINALES_DIR, $env:RESPALDO_DIR) | Where-Object { $_ }
    $llenos = foreach ($unidad in ($rutas | ForEach-Object { [IO.Path]::GetPathRoot($_) } | Sort-Object -Unique)) {
        $disco = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$($unidad.TrimEnd('\'))'"
        if ($disco -and ($disco.FreeSpace / $disco.Size * 100) -lt $UmbralDisco) { "$($disco.DeviceID) con menos del $UmbralDisco % libre" }
    }
    $llenos -join '; '
}

foreach ($problema in $problemas) {
    Write-Output "FALLA   $problema"
    Write-ErpEvento -Mensaje $problema -Tipo Warning -Id 1000
}
if ($problemas.Count) { exit 1 }
