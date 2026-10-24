# No launcher credentials are read by this installer.
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$script:Utf8 = New-Object Text.UTF8Encoding($false)
function Write-TextAtomic($Path, $Text) {
    $temp = $Path + '.' + [Guid]::NewGuid().ToString('N') + '.tmp'
    [IO.File]::WriteAllText($temp, $Text, $script:Utf8)
    if ([IO.File]::Exists($Path)) { [IO.File]::Replace($temp, $Path, [System.Management.Automation.Language.NullString]::Value) }
    else { [IO.File]::Move($temp, $Path) }
}

function Write-JsonAtomic($Path, $Value) {
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Path))
    $temp = $Path + '.' + [Guid]::NewGuid().ToString('N') + '.tmp'
    [IO.File]::WriteAllText($temp, ($Value | ConvertTo-Json -Depth 80), $script:Utf8)
    if ([IO.File]::Exists($Path)) { [IO.File]::Replace($temp, $Path, [System.Management.Automation.Language.NullString]::Value) }
    else { [IO.File]::Move($temp, $Path) }
}

function Get-VirgosClientMemoryMb { return 8192 }

function Resolve-VirgosClientMemoryMb([int]$RequestedMemoryMb) {
    if ($RequestedMemoryMb -lt 4096 -or $RequestedMemoryMb -gt 8192) { throw 'Memoria no valida.' }
    # Managed installations upgrade legacy selections without changing setter APIs.
    return Get-VirgosClientMemoryMb
}

function Update-VirgosClientMemoryPreference([string]$Path) {
    $prefs=Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $prefs -or $prefs -is [Array] -or $prefs -is [string]) { throw 'Las preferencias no son validas.' }
    if ($prefs.memoryMb -ne (Get-VirgosClientMemoryMb)) {
        Copy-Item -LiteralPath $Path -Destination ($Path+'.memoria-'+[Guid]::NewGuid().ToString('N')+'.bak')
        $prefs | Add-Member -NotePropertyName memoryMb -NotePropertyValue (Get-VirgosClientMemoryMb) -Force
        Write-JsonAtomic $Path $prefs
    }
    return $prefs
}

function Save-VirgosClientPreferences([string]$Path,[Collections.IDictionary]$Request) {
    $Request.memoryMb=Resolve-VirgosClientMemoryMb ([int]$Request.memoryMb)
    $prefs=if([IO.File]::Exists($Path)){Update-VirgosClientMemoryPreference $Path}else{[pscustomobject]@{}}
    foreach($entry in $Request.GetEnumerator()) {
        $prefs | Add-Member -NotePropertyName $entry.Key -NotePropertyValue $entry.Value -Force
    }
    Write-JsonAtomic $Path $prefs
}

function Get-FileDigest([string]$Path, [string]$Algorithm = 'SHA512') {
    $hasher = [Security.Cryptography.HashAlgorithm]::Create($Algorithm)
    $stream = [IO.File]::OpenRead($Path)
    try { return ([BitConverter]::ToString($hasher.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
    finally { $stream.Dispose(); $hasher.Dispose() }
}

function Get-ManagedUpgradePlan([string]$GameDir, $Manifest) {
    $mods = Join-Path $GameDir 'mods'
    $oldPath = Join-Path $GameDir 'virgos-cliente.lock.json'
    $known = @($Manifest.files | ForEach-Object { $_.filename })
    $oldFiles = @{}
    if (Test-Path -LiteralPath $oldPath) {
        $old = Get-Content -LiteralPath $oldPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($old.minecraft -ne '1.20.1' -or $old.forge -ne '47.4.22') { throw 'El manifiesto anterior no corresponde a Virgos-MC 1.20.1.' }
        foreach ($item in $old.files) {
            if ([IO.Path]::GetFileName($item.filename) -ne $item.filename -or $item.filename -notmatch '^[A-Za-z0-9_.+ ()-]+\.jar$' -or $item.sha512 -notmatch '^[a-fA-F0-9]{128}$' -or $oldFiles.ContainsKey($item.filename)) { throw 'El manifiesto anterior contiene una entrada invalida.' }
            $oldFiles[$item.filename] = $item.sha512
        }
    }
    $obsolete = New-Object Collections.Generic.List[string]
    if (Test-Path -LiteralPath $mods) {
        if ((Get-Item -LiteralPath $mods).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'La carpeta mods no puede ser un enlace.' }
        foreach ($file in Get-ChildItem -LiteralPath $mods -File -Filter '*.jar') {
            if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Un mod no puede ser un enlace.' }
            if ($file.Name -in $known) { continue }
            if (-not $oldFiles.ContainsKey($file.Name)) { throw 'La carpeta contiene otros mods. Elegi una carpeta nueva para Virgos-MC.' }
            if ((Get-FileDigest $file.FullName) -ne $oldFiles[$file.Name]) { throw "El mod anterior $($file.Name) fue modificado. Se conserva; revisalo antes de actualizar." }
            $obsolete.Add($file.Name)
        }
    }
    return @($obsolete.ToArray())
}

function Set-InstallStatus([int]$Percent, [string]$Message, [string]$State = 'running') {
    Write-Host $Message
    if ($script:StatusPath) { Write-JsonAtomic $script:StatusPath @{percent=$Percent; message=$Message; state=$State} }
}

function Get-VerifiedDownload([string]$Url, [string]$Path, [string]$Hash, [string]$Algorithm = 'SHA512') {
    $uri = [Uri]$Url
    if ($uri.Scheme -ne 'https' -or $uri.Host -notin @('cdn.modrinth.com','edge.forgecdn.net','github.com','maven.minecraftforge.net','piston-meta.mojang.com')) { throw 'Origen de descarga inesperado. Pedi una copia nueva del instalador.' }
    if ((Test-Path -LiteralPath $Path) -and (Get-FileDigest $Path $Algorithm) -eq $Hash) { return }
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Path))
    for ($attempt=1; $attempt -le 3; $attempt++) {
        $client = New-Object Net.WebClient
        $client.Headers['User-Agent'] = 'VirgosMC-Installer/2'
        try {
            $client.DownloadFile($Url, ($Path+'.part'))
            if ((Get-FileDigest ($Path+'.part') $Algorithm) -ne $Hash) { throw 'El archivo descargado no coincide con la version del paquete.' }
            if ([IO.File]::Exists($Path)) { [IO.File]::Replace(($Path+'.part'), $Path, [System.Management.Automation.Language.NullString]::Value) }
            else { [IO.File]::Move(($Path+'.part'), $Path) }
            return
        } catch {
            if ($attempt -eq 3) { throw "No se pudo descargar $([IO.Path]::GetFileName($Path)). Revisa Internet y toca Reintentar. Detalle: $($_.Exception.Message)" }
            Write-Host "Reintentando descarga ($attempt/3)..."
            Start-Sleep -Seconds 2
        } finally { $client.Dispose() }
    }
}

function Set-VirgosProfile([string]$Path, [string]$GameDir, [string]$JavaPath, [int]$MemoryMb) {
    if ($MemoryMb -lt 4096 -or $MemoryMb -gt 8192) { throw 'Memoria fuera del rango permitido.' }
    if ([IO.File]::Exists($Path)) {
        $data = [IO.File]::ReadAllText($Path) | ConvertFrom-Json
        if (-not $data -or $data -is [Array] -or $data -is [string]) { throw 'El archivo de perfiles del launcher no es valido.' }
        Copy-Item -LiteralPath $Path -Destination ($Path+'.virgos-'+[DateTime]::Now.ToString('yyyyMMdd-HHmmssfff')+'.bak')
    } else { $data = [pscustomobject]@{} }
    if (-not $data.PSObject.Properties['profiles']) { $data | Add-Member profiles ([pscustomobject]@{}) }
    if (-not $data.profiles -or $data.profiles -is [Array] -or $data.profiles -is [string]) { throw 'La lista de perfiles no es valida.' }
    $stamp = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
    $profile = [pscustomobject]@{name='Virgos-MC';type='custom';created=$stamp;lastUsed=$stamp;icon='Grass';lastVersionId='1.20.1-forge-47.4.22';gameDir=$GameDir;javaDir=$JavaPath;javaArgs="-Xms1G -Xmx${MemoryMb}M -XX:+UseG1GC"}
    $data.profiles | Add-Member -NotePropertyName 'virgos-mc-1.20.1' -NotePropertyValue $profile -Force
    Write-JsonAtomic $Path $data
}

function Disable-TLauncherShaders([string]$GameDir, [string]$BackupRoot) {
    $path = Join-Path $GameDir 'config\oculus.properties'
    if(-not [IO.File]::Exists($path)) { return $false }
    $text = [IO.File]::ReadAllText($path)
    $active = ($text -match '(?m)^\s*enableShaders\s*=\s*true\s*$') -or ($text -match '(?m)^\s*shaderPack\s*=\s*\S+')
    if(-not $active) { return $false }
    $backupDir = Join-Path $BackupRoot 'tlauncher-shaders'
    [void][IO.Directory]::CreateDirectory($backupDir)
    $backup = Join-Path $backupDir ('oculus-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmssfff')+'.properties.bak')
    Copy-Item -LiteralPath $path -Destination $backup -Force
    $changed = [regex]::Replace($text, '(?m)^\s*shaderPack\s*=.*$', 'shaderPack=')
    if($changed -match '(?m)^\s*enableShaders\s*=') { $changed = [regex]::Replace($changed, '(?m)^\s*enableShaders\s*=.*$', 'enableShaders=false') }
    else { $changed = $changed.TrimEnd("`r","`n") + "`r`nenableShaders=false`r`n" }
    Write-TextAtomic $path $changed
    return $true
}

function Copy-Platform([string]$Source, [string]$Target) {
    # Never copy staging profiles/accounts into the user's launcher.
    foreach ($relative in @('libraries','versions\1.20.1','versions\1.20.1-forge-47.4.22')) {
        $sourceDir = Join-Path $Source $relative
        foreach ($file in Get-ChildItem -LiteralPath $sourceDir -File -Recurse) {
            $destination = Join-Path $Target $file.FullName.Substring($Source.Length).TrimStart('\')
            [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination))
            if (-not [IO.File]::Exists($destination) -or (Get-FileDigest $destination) -ne (Get-FileDigest $file.FullName)) { Copy-Item -LiteralPath $file.FullName -Destination $destination -Force }
        }
    }
}

function Get-LauncherInstructions([string]$Launcher, [string]$GameDir, [string]$JavaPath, [int]$MemoryMb) {
    if ($Launcher -eq 'Oficial') {
        return "1. Abri Minecraft Launcher y entra con tu cuenta habitual.`r`n2. En Minecraft Java, elegi Virgos-MC y toca Jugar.`r`n   Si no aparece: Instalaciones > activa Modificadas.`r`n3. Multijugador > Virgos-MC.`r`n`r`nLa primera vez el launcher descarga los archivos restantes del juego."
    }
    return "DESPUES DE INSTALAR:`r`n1. Abri tu TLauncher habitual con el boton Abrir mi launcher.`r`n2. Forge 1.20.1-forge-47.4.22 queda seleccionado. Toca Entrar al juego.`r`n3. En Minecraft: Multijugador > Virgos-MC.`r`n`r`nPreparamos carpeta, $MemoryMb MB, Forge y Java automatico (el JRE de TLauncher).`r`nLa primera entrada se prepara sin shaders para evitar cierres; luego podes activarlos desde Opciones > Shaders.`r`nNo elijas ForgeOptiFine ni otro paquete de TL MODS.`r`n`r`nLa carpeta general de TLauncher pasa a ser la de Virgos-MC.`r`nTus otras partidas se conservan. Para volver a los ajustes anteriores,`r`ncerra TLauncher y usa Restaurar TL. Instalar vuelve a activar Virgos.`r`n`r`nSi TLauncher nunca se abrio, abrilo una vez y cerralo antes de instalar."
}
