param([Parameter(Mandatory=$true)][string]$RequestPath)
. (Join-Path $PSScriptRoot 'installer-common.ps1')
. (Join-Path $PSScriptRoot 'tlauncher-settings.ps1')
$request = Get-Content -LiteralPath $RequestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$script:StatusPath = $request.statusPath
$base = [IO.Path]::GetFullPath($request.installRoot).TrimEnd('\')
$game = Join-Path $base 'juego'
$cache = Join-Path $base 'descargas'
$logs = Join-Path $base 'registros'
$lockStream = $null
try {
    if ($request.launcher -notin @('Oficial','TLauncher')) { throw 'Elegi tu launcher.' }
    if (-not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { throw 'Este instalador necesita Windows x64 (Intel o AMD).' }
    if ($base -match '[!"\r\n]') { throw 'Elegi una carpeta sin signos de admiracion ni comillas.' }
    if ($base -eq [IO.Path]::GetPathRoot($base).TrimEnd('\')) { throw 'Elegi una subcarpeta para Virgos-MC.' }
    [void][IO.Directory]::CreateDirectory($base)
    $lockStream = [IO.File]::Open((Join-Path $base '.instalando'), 'OpenOrCreate', 'ReadWrite', 'None')
    [void][IO.Directory]::CreateDirectory($logs)
    Start-Transcript -LiteralPath (Join-Path $logs 'instalacion.log') -Force | Out-Null
    if (Get-Process -Name MinecraftLauncher,TLauncher -ErrorAction SilentlyContinue) { throw 'Cierra el launcher antes de instalar. Luego toca Reintentar.' }
    $gameProcesses = Get-CimInstance Win32_Process -Filter "Name='java.exe' OR Name='javaw.exe'" -ErrorAction SilentlyContinue
    if (@($gameProcesses | Where-Object { $_.CommandLine -and $_.CommandLine.IndexOf($game,[StringComparison]::OrdinalIgnoreCase) -ge 0 -and $_.CommandLine -match 'forgeclient|net\.minecraft\.client' }).Count) { throw 'Cierra Minecraft antes de actualizar esta carpeta. Luego toca Reintentar.' }
    $memory = Resolve-VirgosClientMemoryMb ([int]$request.memoryMb)
    $tlConfig=if($request.tlauncherConfig){[IO.Path]::GetFullPath($request.tlauncherConfig)}else{Find-TLauncherSettingsPath}
    if($request.launcher -eq 'TLauncher'){Assert-TLauncherClosed;[void](Read-TLauncherSettings $tlConfig)}
    $runtime = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'runtime.lock.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if (Test-Path -LiteralPath (Join-Path $game 'mods')) {
        $newManifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'cliente.lock.json') -Raw -Encoding UTF8 | ConvertFrom-Json
        [void](Get-ManagedUpgradePlan $game $newManifest)
    }
    $official = [IO.Path]::GetFullPath($request.officialRoot)
    if ($request.launcher -eq 'Oficial') {
        $profileFiles = @('launcher_profiles.json','launcher_profiles_microsoft_store.json') | ForEach-Object { Join-Path $official $_ } | Where-Object { Test-Path -LiteralPath $_ }
        if (-not $profileFiles) { throw 'Abri Minecraft Launcher oficial una vez, inicia sesion y cerralo. Luego toca Reintentar. Si usas otra carpeta, elegila en Opciones.' }
        foreach ($path in $profileFiles) { [void](Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json) }
    }
    Set-InstallStatus 5 '1 de 4 - Descargando Java 17 para Virgos-MC...'
    $javaZip = Join-Path $cache $runtime.java.file
    Get-VerifiedDownload $runtime.java.url $javaZip $runtime.java.hash 'SHA256'
    $runtimeDir = Join-Path $base 'runtime'
    [void][IO.Directory]::CreateDirectory($runtimeDir)
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $java = Join-Path $runtimeDir ($runtime.java.folder+'\bin\java.exe')
    $javaMarker = Join-Path $runtimeDir 'verificado.json'
    $extract = $true
    if ([IO.File]::Exists($javaMarker) -and [IO.File]::Exists($java)) {
        $marker = Get-Content -LiteralPath $javaMarker -Raw | ConvertFrom-Json
        $extract = ($marker.archiveHash -ne $runtime.java.hash -or $marker.javaHash -ne (Get-FileDigest $java))
    }
    if ($extract) {
        Set-InstallStatus 12 'Preparando Java 17...'
        $archive = [IO.Compression.ZipFile]::OpenRead($javaZip)
        try {
            foreach ($entry in $archive.Entries) {
                $out = [IO.Path]::GetFullPath((Join-Path $runtimeDir $entry.FullName))
                if (-not $out.StartsWith($runtimeDir+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Ruta de Java invalida.' }
                if (-not $entry.Name) { [void][IO.Directory]::CreateDirectory($out); continue }
                [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($out))
                [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $out, $true)
            }
        } finally { $archive.Dispose() }
        Write-JsonAtomic $javaMarker @{archiveHash=$runtime.java.hash;javaHash=(Get-FileDigest $java)}
    }
    Set-InstallStatus 18 '2 de 4 - Descargando Forge 1.20.1...'
    $forgeJar = Join-Path $cache $runtime.forge.file
    Get-VerifiedDownload $runtime.forge.url $forgeJar $runtime.forge.hash 'SHA256'
    [void][IO.Directory]::CreateDirectory($game)
    Get-VerifiedDownload $runtime.minecraftJson.url (Join-Path $game 'versions\1.20.1\1.20.1.json') $runtime.minecraftJson.hash 'SHA256'
    # Forge operates in our folder, preserving all existing launcher profiles.
    if (-not [IO.File]::Exists((Join-Path $game 'launcher_profiles.json'))) { Write-JsonAtomic (Join-Path $game 'launcher_profiles.json') @{profiles=@{}} }
    Set-InstallStatus 22 'Instalando Forge. Puede tardar varios minutos; espera...'
    $forgeOut = Join-Path $logs 'forge.log'
    $forgeErr = Join-Path $logs 'forge-error.log'
    $startInfo = New-Object Diagnostics.ProcessStartInfo
    $startInfo.FileName=$java
    $startInfo.Arguments='-Djava.awt.headless=true -jar "'+$forgeJar+'" --installClient "'+$game+'"'
    $startInfo.WorkingDirectory=$cache; $startInfo.UseShellExecute=$false; $startInfo.CreateNoWindow=$true
    $startInfo.RedirectStandardOutput=$true; $startInfo.RedirectStandardError=$true
    $process = New-Object Diagnostics.Process
    $process.StartInfo=$startInfo; [void]$process.Start()
    # Drain both streams asynchronously: Forge prints thousands of processor lines.
    $stdoutTask=$process.StandardOutput.ReadToEndAsync()
    $stderrTask=$process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    [IO.File]::WriteAllText($forgeOut,$stdoutTask.Result,$script:Utf8)
    [IO.File]::WriteAllText($forgeErr,$stderrTask.Result,$script:Utf8)
    if ($process.ExitCode -ne 0 -or -not (Select-String -LiteralPath $forgeOut -SimpleMatch 'Successfully installed client' -Quiet)) { throw 'Forge no termino de instalarse. Revisa Internet y toca Reintentar. El detalle esta en registros\forge.log.' }
    & (Join-Path $PSScriptRoot 'instalar-cliente.ps1') -Destino $game -StatusFile $script:StatusPath
    Set-InstallStatus 95 '4 de 4 - Preparando tu launcher...'
    $javaw = Join-Path ([IO.Path]::GetDirectoryName($java)) 'javaw.exe'
    $shadersDisabled = $false
    if ($request.launcher -eq 'Oficial') {
        if (Get-Process -Name MinecraftLauncher -ErrorAction SilentlyContinue) { throw 'El launcher se abrio durante la instalacion. Cerralo y toca Reintentar para guardar el perfil.' }
        Copy-Platform $game $official
        foreach ($path in $profileFiles) { Set-VirgosProfile $path $game $javaw $memory }
    } else {
        $shadersDisabled = Disable-TLauncherShaders $game (Join-Path $base 'respaldos-launcher')
        [void](Set-VirgosTLauncher $tlConfig $game $memory (Join-Path $base 'respaldos-launcher'))
    }
    $steps = Get-LauncherInstructions $request.launcher $game $javaw $memory
    [IO.File]::WriteAllText((Join-Path $base 'COMO-ENTRAR.txt'), $steps, (New-Object Text.UTF8Encoding($true)))
    $installedPack = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'cliente.lock.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    Write-JsonAtomic (Join-Path $base 'instalacion.json') @{launcher=$request.launcher;gameDir=$game;java=$javaw;memoryMb=$memory;pack=$installedPack.version;installer=$installedPack.installerVersion;tlauncherConfigured=($request.launcher -eq 'TLauncher');shadersSafeMode=$shadersDisabled;completedUtc=[DateTime]::UtcNow.ToString('o')}
    Set-InstallStatus 100 'Instalacion terminada. Segui los pasos de abajo para entrar.' 'complete'
} catch {
    Set-InstallStatus 0 $_.Exception.Message 'error'
    Write-Host $_.ScriptStackTrace
    exit 1
} finally {
    try { Stop-Transcript | Out-Null } catch {}
    if ($lockStream) { $lockStream.Dispose() }
}
