param(
    [string]$TokenFile,
    [switch]$ValidateOnly
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'archivos.ps1')
$utf8 = New-Object Text.UTF8Encoding($false)
$manifest = Get-Content -LiteralPath (Join-Path $root 'pack/discordsrv.lock.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$cache = Join-Path $root ('.cache/pack/downloads/' + $manifest.filename)
$templates = Join-Path $root 'templates/discordsrv'
$names = @('config.yml', 'messages.yml', 'synchronization.yml', 'linking.yml', 'voice.yml', 'alerts.yml')
foreach ($name in $names) {
    if (-not (Test-Path -LiteralPath (Join-Path $templates $name))) { throw "Falta la plantilla DiscordSRV: $name" }
}
if (-not (Test-Path -LiteralPath $cache)) {
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($cache))
    Invoke-WebRequest -Uri $manifest.url -OutFile $cache -UseBasicParsing
}
if ((Get-VerifiedHash -Path $cache -Algorithm $manifest.hash_algorithm) -ne $manifest.hash) { throw 'DiscordSRV no coincide con el archivo oficial verificado.' }
if ($ValidateOnly) {
    Write-Output 'OK: plantillas y DiscordSRV 1.30.5 verificados. Sin cambios en el servidor.'
    return
}

# Require a clean stop before changing plugin files or the delivery manifest.
$stateFile = Join-Path $root '.runtime/active-run.json'
if (Test-Path -LiteralPath $stateFile) {
    $state = Get-Content -LiteralPath $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($state.backupInProgress -or $state.backupError) { throw 'Espera a que termine correctamente el respaldo del servidor.' }
    if (-not $state.finished -and (Get-Process -Id $state.pid -ErrorAction SilentlyContinue)) { throw 'Primero detene el servidor con detener.bat y espera su respaldo.' }
}
$listeners = [Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
if (@($listeners | Where-Object { $_.Port -eq 25565 }).Count -gt 0) {
    throw 'El puerto 25565 sigue ocupado. Detene Minecraft antes de configurar Discord.'
}

$token = $null
try {
    if ($TokenFile) {
        $token = [IO.File]::ReadAllText([IO.Path]::GetFullPath($TokenFile), $utf8).Trim()
    } else {
        $secure = Read-Host 'Pega el BOT TOKEN de Virgos-MC (no se mostrara)' -AsSecureString
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        try { $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer).Trim() }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $secure.Dispose() }
    }
    if ($token.Length -lt 59 -or $token -notmatch '^[A-Za-z0-9_.-]+$') { throw 'El valor no tiene formato de bot token. No uses el Client Secret.' }
    # Read-only checks against Discord. Never display the token or HTTP headers.
    try {
        $headers = @{ Authorization = 'Bot ' + $token }
        $bot = Invoke-RestMethod 'https://discord.com/api/v10/users/@me' -UserAgent 'VirgosMC-Setup/1.0' -Headers $headers
        $channel = Invoke-RestMethod 'https://discord.com/api/v10/channels/1561436921006137527' -UserAgent 'VirgosMC-Setup/1.0' -Headers $headers
    } catch { throw 'Discord no acepto el token o el bot no puede ver #virgos-mc. Revisa su invitacion y permisos.' }
    if (-not $bot.bot -or $bot.id -ne '1561500718144299008' -or $channel.guild_id -ne '736709362206113802' -or $channel.type -ne 0) { throw 'El bot o el canal no corresponden a la configuracion esperada de LaLechebanda.' }

    $target = Join-Path $root 'plugins/DiscordSRV'
    $lockPath = Join-Path $root 'pack/administration.lock.json'
    $oldLock = [IO.File]::ReadAllText($lockPath, $utf8)
    $entries = $oldLock | ConvertFrom-Json
    $old = @($entries | Where-Object { $_.project -eq 'discordsrv' })
    if ($old.Count -gt 0 -and $old[0].filename -ne $manifest.filename) { throw 'Ya hay otra version de DiscordSRV; requiere migracion explicita.' }
    $backup = Join-Path $root ('backups/discord/config-' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss-fff'))
    [void][IO.Directory]::CreateDirectory($backup)
    [IO.File]::WriteAllText((Join-Path $backup 'administration.lock.json'), $oldLock, $utf8)
    if (Test-Path -LiteralPath $target) { Copy-Item -LiteralPath $target -Destination (Join-Path $backup 'DiscordSRV') -Recurse }
    [void][IO.Directory]::CreateDirectory($target)
    foreach ($name in $names) { Copy-Item -LiteralPath (Join-Path $templates $name) -Destination (Join-Path $target $name) -Force }
    # DiscordSRV supports this separate local secret file natively.
    $privateTokenPath = Join-Path $target '.token'
    [IO.File]::WriteAllText($privateTokenPath, $token, $utf8)
    $privateAcl = New-Object Security.AccessControl.FileSecurity
    $privateAcl.SetAccessRuleProtection($true, $false)
    $owner = [Security.Principal.WindowsIdentity]::GetCurrent().User
    $privateAcl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($owner, 'FullControl', 'Allow')))
    [IO.File]::SetAccessControl($privateTokenPath, $privateAcl)
    Copy-Item -LiteralPath $cache -Destination (Join-Path $root ('plugins/' + $manifest.filename)) -Force
    $entries = @($entries | Where-Object { $_.project -ne 'discordsrv' }) + @($manifest)
    [IO.File]::WriteAllText($lockPath, (ConvertTo-Json -InputObject $entries -Depth 10) + [Environment]::NewLine, $utf8)
    & (Join-Path $PSScriptRoot 'validar-entrega.ps1') -ServerPath $root
    Write-Output 'DiscordSRV instalado y token validado. Inicia el servidor para comprobar la conexion y ambos sentidos del chat.'
} finally {
    $token = $null
    $headers = $null
}
