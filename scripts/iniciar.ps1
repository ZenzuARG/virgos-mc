# VIRGOS-INTEGRAL-1
param(
    [ValidatePattern('^[1-9][0-9]*[MG]$')][string]$InitialMemory = '1G',
    [ValidatePattern('^[1-9][0-9]*[MG]$')][string]$MaxMemory = '8G',
    [switch]$ValidateOnly
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'archivos.ps1')
. (Join-Path $PSScriptRoot 'server-lock.ps1')
$serverLease=$null
$root = Split-Path -Parent $PSScriptRoot
$lock = Get-Content -LiteralPath (Join-Path $root 'versions.lock.json') -Raw | ConvertFrom-Json
$java = Join-Path $root ('.runtime\' + $lock.java.folder + '\bin\java.exe')
$launcher = Join-Path $root 'ketting-server.jar'
$eula = Join-Path $root 'eula.txt'

try {
    & (Join-Path $PSScriptRoot 'validar-entrega.ps1') -ServerPath $root -Quiet
    if ($ValidateOnly) { Write-Output 'Java, launcher, todos los mods/plugins y EULA comprobados.'; exit 0 }
    $serverLease=Enter-ServerLock -Root $root
    $statePath = Join-Path $root '.runtime/active-run.json'
    if (Test-Path -LiteralPath $statePath) {
        $previous = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
        $ownerId = if($previous.backupInProgress) { $previous.runner } elseif(-not $previous.finished) { $previous.pid } else { $null }
        if ($ownerId -and (Get-Process -Id $ownerId -ErrorAction SilentlyContinue)) {
            throw 'El servidor esta en ejecucion o verificando un respaldo.'
        }
    }
    $probe = New-Object Net.Sockets.TcpClient
    try {
        $portLine = Get-Content -LiteralPath (Join-Path $root 'server.properties') | Where-Object { $_ -match '^server-port=' } | Select-Object -First 1
        $port = if ($portLine) { [int]($portLine -split '=',2)[1] } else { 25565 }
        try { $connection = $probe.ConnectAsync('127.0.0.1', $port); [void]$connection.Wait(500) } catch { }
        if ($probe.Connected) { throw "El puerto $port ya esta ocupado. No se iniciara otra instancia." }
    } finally { $probe.Dispose() }
    Push-Location $root
    try {
      do {
        & (Join-Path $PSScriptRoot 'validar-entrega.ps1') -ServerPath $root -Quiet
        $runStarted=(Get-Date).ToUniversalTime().ToString('o')
        @{mode='console';checkpointSupport=$true;pid=$PID;started=$runStarted} | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
        Write-Host "Virgos-MC | Minecraft $($lock.minecraft) / Forge $($lock.forge) / Ketting $($lock.ketting)"
        Write-Host "RAM: $InitialMemory inicial, $MaxMemory maxima. Para apagar y guardar, escribe stop."
        & $java "-Xms$InitialMemory" "-Xmx$MaxMemory" '-XX:+UseParallelGC' '-Xlog:gc:file=.runtime/gc-server.log:time,level,tags:filecount=3,filesize=2M' '-Dfile.encoding=UTF-8' '-jar' $launcher '-minecraftVersion' $lock.minecraft '-forgeVersion' $lock.forge '-kettingVersion' $lock.ketting '-daul' '-dau' '-noui' 'nogui'
        $result = $LASTEXITCODE
        @{mode='console';pid=$PID;runner=$PID;backupInProgress=($result -eq 0);finished=(Get-Date).ToUniversalTime().ToString('o');exitCode=$result} | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
        $restart=$false
        if($result -eq 0) {
            Write-Host 'Guardado terminado. Verificando el respaldo completo...'
            $completion=(& (Join-Path $PSScriptRoot 'finalizar-ejecucion.ps1') -RunStarted $runStarted -ExitCode $result) | ConvertFrom-Json
            Write-Host "Respaldo completo: $($completion.backup)"
            $restart=$completion.restart
        }
      } while($restart)
    } finally {
        @{pid=$PID;finished=(Get-Date).ToUniversalTime().ToString('o');exitCode=$result} | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
        Pop-Location
    }
    exit $result
} catch {
    Write-Host "La operacion del servidor no pudo completarse: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    Exit-ServerLock $serverLease
}

