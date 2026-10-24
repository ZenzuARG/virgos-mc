$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$node = (Get-Command node -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$statePath = Join-Path $root '.runtime/active-run.json'
if (Test-Path -LiteralPath $statePath) {
    $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
    $ownerId = if ($state.backupInProgress) { $state.runner } elseif (-not $state.finished) { $state.pid } else { $null }
    if ($ownerId -and (Get-Process -Id $ownerId -ErrorAction SilentlyContinue)) {
        throw 'El servidor sigue activo o esta realizando su respaldo.'
    }
}
$runner = Start-Process -FilePath $node -ArgumentList @('scripts/run-public.cjs') -WorkingDirectory $root -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $root '.runtime/runner.log') -RedirectStandardError (Join-Path $root '.runtime/runner-error.log')
Write-Output "Arranque solicitado en segundo plano (controlador $($runner.Id)). Revisa .runtime/runner.log y logs/latest.log; usa detener.bat para guardar y apagar."
