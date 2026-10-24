$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'archivos.ps1')
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$root = Split-Path -Parent $PSScriptRoot
$lock = Get-Content -LiteralPath (Join-Path $root 'versions.lock.json') -Raw | ConvertFrom-Json

function Get-VerifiedAsset($Asset) {
    if ($Asset.local_path) {
        $localAsset = Join-Path $root $Asset.local_path
        if (-not (Test-Path -LiteralPath $localAsset) -or (Get-VerifiedHash -Path $localAsset -Algorithm $Asset.algorithm) -ne $Asset.hash) {
            throw "Falta o cambio el componente local verificado: $($Asset.local_path)"
        }
        return $localAsset
    }
    $destination = Join-Path $root ('.cache\' + $Asset.file)
    if (-not (Test-Path -LiteralPath $destination)) {
        $temporary = $destination + '.download'
        Write-Host "Descargando $($Asset.file)..."
        Invoke-WebRequest -Uri $Asset.url -OutFile $temporary -UseBasicParsing
        if ((Get-VerifiedHash -Path $temporary -Algorithm $Asset.algorithm) -ne $Asset.hash) {
            throw "La descarga no coincide con el hash publicado: $($Asset.file)"
        }
        Move-Item -LiteralPath $temporary -Destination $destination -Force
    }
    if ((Get-VerifiedHash -Path $destination -Algorithm $Asset.algorithm) -ne $Asset.hash) {
        throw "Archivo alterado o incompleto: $destination"
    }
    return $destination
}

Push-Location $root
try {
    foreach ($folder in @('.cache', '.runtime', 'mods', 'plugins', 'config', 'backups')) {
        New-Item -ItemType Directory -Path (Join-Path $root $folder) -Force | Out-Null
    }
    $javaArchive = Get-VerifiedAsset $lock.java
    $java = Join-Path $root ('.runtime\' + $lock.java.folder + '\bin\java.exe')
    if (-not (Test-Path -LiteralPath $java)) {
        Expand-Archive -LiteralPath $javaArchive -DestinationPath (Join-Path $root '.runtime') -Force
    }
    if (-not (Test-Path -LiteralPath $java)) { throw 'No se encontro Java en el runtime extraido.' }
    $launcher = Get-VerifiedAsset $lock.launcher
    Copy-Item -LiteralPath $launcher -Destination (Join-Path $root 'ketting-server.jar') -Force
    foreach ($component in @(@{asset=$lock.authMe;folder='plugins'}, @{asset=$lock.playitCompanion;folder='mods'})) {
        $assetFile = Get-VerifiedAsset $component.asset
        Copy-Item -LiteralPath $assetFile -Destination (Join-Path $root ($component.folder + '\' + $component.asset.file)) -Force
        foreach ($oldFile in $component.asset.replaces) {
            $oldPath = Join-Path $root ($component.folder + '\' + $oldFile)
            if (Test-Path -LiteralPath $oldPath) {
                $savedPath = Join-Path $root ('backups\' + $oldFile + '.superseded')
                if (-not (Test-Path -LiteralPath $savedPath)) { Copy-Item -LiteralPath $oldPath -Destination $savedPath }
                Remove-Item -LiteralPath $oldPath
            }
        }
    }
    $authConfig = Join-Path $root 'plugins\AuthMe\config.yml'
    if (-not (Test-Path -LiteralPath $authConfig)) {
        New-Item -ItemType Directory -Path (Split-Path -Parent $authConfig) -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $root 'templates\AuthMe\config.yml') -Destination $authConfig
    }
    $welcome = Join-Path $root 'plugins\AuthMe\welcome.txt'
    if (-not (Test-Path -LiteralPath $welcome)) {
        Copy-Item -LiteralPath (Join-Path $root 'templates\AuthMe\welcome.txt') -Destination $welcome
    }
    if (-not (Test-Path -LiteralPath (Join-Path $root 'server.properties'))) {
        Copy-Item -LiteralPath (Join-Path $root 'server.properties.example') -Destination (Join-Path $root 'server.properties')
    }
    if (-not (Test-Path -LiteralPath (Join-Path $root 'eula.txt'))) {
        @('# Read https://www.minecraft.net/eula before accepting.', 'eula=false') |
            Set-Content -LiteralPath (Join-Path $root 'eula.txt') -Encoding ASCII
    }
    # This only installs dependencies. It does not accept the EULA or start a world.
    & $java '-Xmx2G' '-jar' 'ketting-server.jar' '-minecraftVersion' $lock.minecraft '-forgeVersion' $lock.forge '-kettingVersion' $lock.ketting '-daul' '-dau' '-noui' '-installOnly'
    if ($LASTEXITCODE -ne 0) { throw "La instalacion fallo: codigo $LASTEXITCODE" }
    Write-Host 'Preparacion terminada. Para jugar, revisa el EULA y ejecuta iniciar.bat.' -ForegroundColor Green
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

