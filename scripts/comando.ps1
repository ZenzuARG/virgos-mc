param([string]$Comando)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$stateFile=Join-Path $root '.runtime/active-run.json'
if (-not (Test-Path -LiteralPath $stateFile)) { throw 'No hay un servidor administrado en ejecucion.' }
$state=Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json
if ($state.mode -ne 'managed' -or $state.finished -or -not (Get-Process -Id $state.pid -ErrorAction SilentlyContinue)) {
    throw 'Si iniciaste con iniciar.bat, escribi el comando en esa consola.'
}
if (-not $Comando) { $Comando=Read-Host 'Comando de consola (stop para guardar y apagar)' }
if (-not $Comando -or $Comando -match '[\r\n]') { throw 'Escribi un solo comando.' }
[IO.File]::AppendAllText((Join-Path $root '.runtime/public-commands.txt'),$Comando+"`n",[Text.UTF8Encoding]::new($false))
Write-Host 'Comando enviado. La respuesta aparece en logs/latest.log.'
