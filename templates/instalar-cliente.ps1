param([string]$Destino = (Join-Path $PSScriptRoot 'instancia'), [switch]$Opcionales, [switch]$Verificar, [string]$StatusFile)
. (Join-Path $PSScriptRoot 'installer-common.ps1')
$script:StatusPath = $StatusFile
$manifestPath = Join-Path $PSScriptRoot 'cliente.lock.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$shaderManifestPath = Join-Path $PSScriptRoot 'shaderpack.lock.json'
$shaderManifest = $null
if ([IO.File]::Exists($shaderManifestPath)) {
    $shaderManifest = Get-Content -LiteralPath $shaderManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($shaderManifest.filename -notmatch '^[A-Za-z0-9_.+ ()-]+\.zip$' -or $shaderManifest.sha512 -notmatch '^[a-fA-F0-9]{128}$') { throw 'Shaderpack invalido.' }
    $shaderUri = [Uri]$shaderManifest.url
    if ($shaderUri.Scheme -ne 'https' -or $shaderUri.Host -ne 'cdn.modrinth.com') { throw 'Origen del shaderpack inesperado.' }
}
$target = [IO.Path]::GetFullPath($Destino)
if ($manifest.minecraft -ne '1.20.1' -or $manifest.forge -ne '47.4.22') { throw 'Version de paquete desconocida.' }
$controlsPlan=$null
if(-not $Verificar) {
    # Reject invalid controls before staging downloads, replacing mods or writing the lock.
    $keyHelper=Join-Path $PSScriptRoot 'client-keybindings.ps1'
    $keyPolicy=Join-Path $PSScriptRoot 'keybindings.json'
    if([IO.File]::Exists($keyHelper) -ne [IO.File]::Exists($keyPolicy)) { throw 'El paquete de controles esta incompleto. Extrae nuevamente el ZIP.' }
    if([IO.File]::Exists($keyHelper)) {
        . $keyHelper
        $controlsPlan=Get-VirgosKeyBindingsPlan (Join-Path $target 'options.txt') $keyPolicy (Join-Path $PSScriptRoot 'overrides\options.txt')
    }
}
$dhPlan=$null
if(-not $Verificar) {
    # Pin the patched DH settings before downloads or any installed file changes.
    $dhHelper=Join-Path $PSScriptRoot 'dh-client-settings.ps1'
    $dhDefaults=Join-Path $PSScriptRoot 'overrides\config\DistantHorizons.toml'
    if([IO.File]::Exists($dhHelper) -ne [IO.File]::Exists($dhDefaults)) { throw 'El paquete de ajustes de DH esta incompleto. Extrae nuevamente el ZIP.' }
    if([IO.File]::Exists($dhHelper)) {
        . $dhHelper
        $dhPlan=Get-VirgosDhSettingsPlan (Join-Path $target 'config\DistantHorizons.toml') $dhDefaults
    }
}
$seenNames=@{}
foreach ($item in $manifest.files) {
    if ([IO.Path]::GetFileName($item.filename) -ne $item.filename -or $item.filename -notmatch '^[A-Za-z0-9_.+ ()-]+\.jar$') { throw 'Nombre de mod invalido.' }
    if ($seenNames.ContainsKey($item.filename) -or $item.sha512 -notmatch '^[a-fA-F0-9]{128}$') { throw 'Hash invalido o componente duplicado.' }
    $seenNames[$item.filename]=$true
    if ($item.bundled -eq $true) {
        $versionPattern='[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*)?'
        $knownRole=(($item.project -ceq 'virgos-codex') -and ($item.filename -cmatch ('^virgos_codex-'+$versionPattern+'\.jar$'))) -or
                   (($item.project -ceq 'distant-horizons') -and ($item.filename -ceq 'DistantHorizons-3.3.3-1.20.1-fabric-forge.jar')) -or
                   (($item.project -ceq 'virgos-dh-compat') -and ($item.filename -cmatch ('^virgos_dh_compat-'+$versionPattern+'\.jar$')))
        if (-not $knownRole -or $item.optional) { throw 'Componente incluido inesperado.' }
        $included=Join-Path (Join-Path $PSScriptRoot 'bundled') $item.filename
        if (-not [IO.File]::Exists($included) -or (Get-FileDigest $included) -ne $item.sha512) { throw 'El componente incluido esta incompleto o modificado. Extrae nuevamente el ZIP.' }
    } else {
        $uri = [Uri]$item.url
        if ($uri.Scheme -ne 'https' -or $uri.Host -notin @('cdn.modrinth.com','edge.forgecdn.net')) { throw 'Origen de descarga inesperado.' }
    }
}
$mods = Join-Path $target 'mods'
$selected = @($manifest.files | Where-Object { -not $_.optional -or $Opcionales -or [IO.File]::Exists((Join-Path $mods $_.filename)) })
$obsolete = @(Get-ManagedUpgradePlan $target $manifest)
if ($Verificar -and $obsolete.Count) { throw 'Hay versiones anteriores del paquete. Usa Revisar / reparar para actualizar.' }
if (-not $Verificar) { [void][IO.Directory]::CreateDirectory($mods) }
$stage = Join-Path $target ('.virgos-update\'+[Guid]::NewGuid().ToString('N'))
$replacements = New-Object Collections.Generic.List[object]
$shaderReplacement = $null
$number = 0
foreach ($item in $selected) {
    $number++
    Set-InstallStatus (45+[int](47*$number/$selected.Count)) "Mods: $number de $($selected.Count) - $($item.project)"
    $file = Join-Path $mods $item.filename
    if ($Verificar) {
        if (-not (Test-Path -LiteralPath $file) -or (Get-FileDigest $file) -ne $item.sha512) { throw "Falta o no coincide: $($item.filename)" }
    } elseif (-not [IO.File]::Exists($file) -or (Get-FileDigest $file) -ne $item.sha512) {
        $pending = Join-Path $stage $item.filename
        if ($item.bundled -eq $true) {
            [void][IO.Directory]::CreateDirectory($stage)
            Copy-Item -LiteralPath (Join-Path (Join-Path $PSScriptRoot 'bundled') $item.filename) -Destination $pending
            if ((Get-FileDigest $pending) -ne $item.sha512) { throw 'No se pudo verificar el codice incluido.' }
        } else { Get-VerifiedDownload $item.url $pending $item.sha512 }
        $replacements.Add(@{source=$pending;target=$file;name=$item.filename})
    }
}
if ($shaderManifest) {
    $shaderTarget = Join-Path (Join-Path $target 'shaderpacks') $shaderManifest.filename
    if ($Verificar) {
        if (-not [IO.File]::Exists($shaderTarget) -or (Get-FileDigest $shaderTarget) -ne $shaderManifest.sha512) { throw "Falta o no coincide: $($shaderManifest.filename)" }
    } elseif (-not [IO.File]::Exists($shaderTarget) -or (Get-FileDigest $shaderTarget) -ne $shaderManifest.sha512) {
        $shaderPending = Join-Path (Join-Path $stage 'shaderpacks') $shaderManifest.filename
        Get-VerifiedDownload $shaderManifest.url $shaderPending $shaderManifest.sha512
        $shaderReplacement = @{source=$shaderPending;target=$shaderTarget;name=$shaderManifest.filename}
    }
}
if (-not $Verificar) {
    # Finish every download before touching the installed mods. An interrupted
    # commit is repairable using the previous manifest and retained originals.
    $backup = Join-Path $target ('respaldos-actualizacion\'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmssfff'))
    if ($obsolete.Count -or $replacements.Count) {
        [void][IO.Directory]::CreateDirectory($backup)
        $oldManifest = Join-Path $target 'virgos-cliente.lock.json'
        if (Test-Path -LiteralPath $oldManifest) { Copy-Item -LiteralPath $oldManifest -Destination (Join-Path $backup 'virgos-cliente.lock.json') }
        foreach ($name in $obsolete) { Move-Item -LiteralPath (Join-Path $mods $name) -Destination (Join-Path $backup $name) }
        foreach ($replacement in $replacements) {
            if (Test-Path -LiteralPath $replacement.target) { Move-Item -LiteralPath $replacement.target -Destination (Join-Path $backup $replacement.name) }
            Move-Item -LiteralPath $replacement.source -Destination $replacement.target
        }
        if ($shaderReplacement) {
            [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($shaderReplacement.target))
            if (Test-Path -LiteralPath $shaderReplacement.target) { Move-Item -LiteralPath $shaderReplacement.target -Destination (Join-Path $backup $shaderReplacement.name) }
            Move-Item -LiteralPath $shaderReplacement.source -Destination $shaderReplacement.target
        }
    }
    $overrides = Join-Path $PSScriptRoot 'overrides'
    foreach ($file in Get-ChildItem -LiteralPath $overrides -File -Recurse) {
        $relative = $file.FullName.Substring($overrides.Length).TrimStart('\','/')
        if($dhPlan -and $relative -eq 'config\DistantHorizons.toml') { continue }
        $out = [IO.Path]::GetFullPath((Join-Path $target $relative))
        if (-not $out.StartsWith($target.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Ruta invalida.' }
        if ($relative -in @('servers.dat','options.txt') -and [IO.File]::Exists($out)) { continue }
        if ($relative -eq 'config\voicechat\voicechat-client.properties' -and [IO.File]::Exists($out)) { continue }
        [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($out))
        Copy-Item -LiteralPath $file.FullName -Destination $out -Force
    }
    if($null -ne $dhPlan) { Write-VirgosDhSettingsPlan $dhPlan }
    Write-TextAtomic (Join-Path $target 'virgos-cliente.lock.json') ([IO.File]::ReadAllText($manifestPath))
    if($null -ne $controlsPlan) { Write-VirgosKeyBindingsPlan $controlsPlan }
    # Add only the new voice controls on upgrade. Preserve existing custom bindings.
    # ConvertFrom-Json returns either one object or an array for files, so do
    # not rely on member enumeration when deciding whether this is an older
    # Virgos package.
    $projects = @($manifest.files | ForEach-Object { [string]$_.project })
    $packVersion = [string]$manifest.version
    if ($projects -contains 'simple-voice-chat' -or $packVersion -match '^0\.[23]\.') {
        $optionsPath = Join-Path $target 'options.txt'
        if ([IO.File]::Exists($optionsPath)) {
            $text = [IO.File]::ReadAllText($optionsPath)
            foreach ($binding in @('key_key.push_to_talk:key.keyboard.caps.lock','key_key.voice_chat:key.keyboard.o')) {
                $key = $binding.Split(':')[0]
                if ($text -notmatch ('(?m)^'+[regex]::Escape($key)+':')) { $text += "`r`n$binding" }
            }
            Write-TextAtomic $optionsPath $text
        }
    }
}
Write-Host "$($selected.Count) mods verificados. Servidor: virgos-mc.playit.plus"
