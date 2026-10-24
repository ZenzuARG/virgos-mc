$ErrorActionPreference='Stop'
$env:PSModulePath="$env:SystemRoot\System32\WindowsPowerShell\v1.0\Modules"
$root=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
. (Join-Path $root 'scripts/server-lock.ps1')
# Uses the same complete archive and per-file verification as a clean shutdown.
# A future timestamp prevents an old checkpoint request from restarting the server.
$lease=$null
$ok=$false
try {
    $lease=Enter-ServerLock -Root $root -Kind backup
    & (Join-Path $root 'scripts/finalizar-ejecucion.ps1') -RunStarted ([DateTime]::UtcNow.AddMinutes(1).ToString('o')) -ExitCode 0 -BackupLabel manual
    $ok=$true
} catch {
    Write-Output $_.Exception.Message
    exit 1
} finally {
    @{pid=$PID;finished=[DateTime]::UtcNow.ToString('o');ok=$ok} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root '.runtime/panel-backup.json') -Encoding UTF8
    Exit-ServerLock $lease
}
