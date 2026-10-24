param([switch]$NoBrowser)
$ErrorActionPreference='Stop'
$env:PSModulePath="$env:SystemRoot\System32\WindowsPowerShell\v1.0\Modules"
$root=Split-Path -Parent $PSScriptRoot
$url='http://127.0.0.1:8765'
function Test-Panel {
    try {
        $health=Invoke-RestMethod -Uri "$url/health" -TimeoutSec 2
        if($health.app -eq 'virgos-admin' -and $health.root -eq $root) {return $true}
        throw 'El puerto 8765 esta ocupado por otra aplicacion.'
    } catch [System.Net.WebException] {return $false}
}
if(-not (Test-Panel)) {
    $node=(Get-Command node -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
    [void][IO.Directory]::CreateDirectory((Join-Path $root '.runtime'))
    $process=Start-Process -FilePath $node -ArgumentList @('--disable-warning=ExperimentalWarning','scripts/admin-panel/server.cjs') -WorkingDirectory $root -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $root '.runtime/admin-panel.log') -RedirectStandardError (Join-Path $root '.runtime/admin-panel-error.log')
    $ready=$false
    for($attempt=0;$attempt -lt 30;$attempt++) {
        Start-Sleep -Milliseconds 250
        if(Test-Panel) {$ready=$true;break}
        if($process.HasExited) {break}
    }
    if(-not $ready) {throw 'No se pudo abrir el panel. Revisa .runtime/admin-panel-error.log. El servidor Minecraft no fue detenido.'}
}
if(-not $NoBrowser) {Start-Process $url}
Write-Output "Panel disponible: $url"
