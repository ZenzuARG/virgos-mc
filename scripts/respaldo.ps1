param(
    [string]$ServerPath = (Split-Path -Parent $PSScriptRoot),
    [ValidatePattern('^[a-z0-9_-]+$')][string]$Label = 'manual'
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'archivos.ps1')
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$serverRoot = [IO.Path]::GetFullPath($ServerPath)
$compressionName = 'Optimal'
$policyPath = Join-Path $serverRoot 'config/virgos/maintenance.json'
if (Test-Path -LiteralPath $policyPath) {
    $policy = Get-Content -LiteralPath $policyPath -Raw | ConvertFrom-Json
    if ($policy.compressionLevel -and $policy.compressionLevel -in @('Optimal','Fastest','NoCompression')) {
        $compressionName = [string]$policy.compressionLevel
    }
}
$compressionLevel = [Enum]::Parse([IO.Compression.CompressionLevel], $compressionName)
if ($serverRoot -ne $projectRoot -and -not $serverRoot.StartsWith($projectRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'El servidor debe estar dentro del proyecto.'
}
$propertiesPath = Join-Path $serverRoot 'server.properties'
if (-not (Test-Path -LiteralPath $propertiesPath)) { throw 'Falta server.properties.' }
$properties = Get-Content -LiteralPath $propertiesPath
$port = 25565
$levelName = 'world'
foreach ($line in $properties) {
    if ($line -match '^server-port=(\d+)$') { $port = [int]$Matches[1] }
    if ($line -match '^level-name=(.+)$') { $levelName = $Matches[1] }
}
if ($levelName -notmatch '^[a-zA-Z0-9_-]+$') { throw 'Nombre de mundo no admitido para el respaldo.' }
foreach ($recordPath in @((Join-Path $serverRoot 'process.json'), (Join-Path $serverRoot '.runtime/active-run.json'))) {
    if (Test-Path -LiteralPath $recordPath) {
        $record = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
        if (-not $record.finished -and $record.pid -and (Get-Process -Id $record.pid -ErrorAction SilentlyContinue)) {
            throw 'Detene el servidor con stop antes de crear una copia consistente.'
        }
    }
}
$probe = New-Object Net.Sockets.TcpClient
try {
    try { $connection = $probe.ConnectAsync('127.0.0.1', $port); [void]$connection.Wait(500) } catch { }
    if ($probe.Connected) { throw "El puerto $port sigue activo. Detene el servidor con stop." }
} finally { $probe.Dispose() }

$destination = Join-Path $projectRoot 'backups/full'
[void][IO.Directory]::CreateDirectory($destination)
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$archivePath = Join-Path $destination ("virgos-$stamp-$Label.zip")
if (Test-Path -LiteralPath $archivePath) { throw 'Ya existe ese respaldo.' }
$temporaryPath = $archivePath + '.partial'
$files = New-Object 'System.Collections.Generic.List[System.IO.FileInfo]'
foreach ($file in Get-ChildItem -LiteralPath $serverRoot -File) {
    if ($file.Name -notin @('console.log', 'console-commands.txt', 'process.json')) { $files.Add($file) }
}
# Ketting stores mod dimensions in sibling world folders as well as DIM folders.
# Enumerate the whole world family so Aether/Twilight/pocket dimensions survive.
$worldFolders = @(Get-ChildItem -LiteralPath $serverRoot -Directory | Where-Object {
    $_.Name -eq $levelName -or $_.Name.StartsWith($levelName + '_', [StringComparison]::OrdinalIgnoreCase)
} | Select-Object -ExpandProperty Name)
if ($worldFolders -notcontains $levelName) { throw 'No se encontro el mundo principal.' }
$folders = $worldFolders + @('mods', 'plugins', 'config', 'defaultconfigs', 'kubejs', 'playit', 'resourcepacks')
if ($serverRoot -eq $projectRoot) { $folders += @('scripts', 'pack', 'docs') }
foreach ($folder in $folders | Select-Object -Unique) {
    $folderPath = Join-Path $serverRoot $folder
    if (Test-Path -LiteralPath $folderPath) {
        $folderInfo = Get-Item -LiteralPath $folderPath
        if ($folderInfo.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "No se copian enlaces: $folderPath" }
        foreach ($file in Get-ChildItem -LiteralPath $folderPath -File -Recurse) {
            if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "No se copian enlaces: $($file.FullName)" }
            $files.Add($file)
        }
    }
}
$manifest = New-Object 'System.Collections.Generic.List[object]'
$output = [IO.File]::Open($temporaryPath, [IO.FileMode]::CreateNew)
$archive = New-Object IO.Compression.ZipArchive($output, [IO.Compression.ZipArchiveMode]::Create, $false)
try {
    foreach ($file in $files | Sort-Object FullName -Unique) {
        $relative = $file.FullName.Substring($serverRoot.Length + 1).Replace('\', '/')
        $entry = $archive.CreateEntry($relative, $compressionLevel)
        # FileInfo may be stale if documentation/configuration changed after
        # enumeration. Hold one read-only handle (no shared writes) for both
        # hashing and copying, and take length from that same opened stream.
        $source = [IO.File]::Open($file.FullName, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
        $target = $entry.Open()
        $algorithm = [Security.Cryptography.SHA256]::Create()
        try {
            $length = $source.Length
            $hash = [BitConverter]::ToString($algorithm.ComputeHash($source)).Replace('-', '').ToLowerInvariant()
            $source.Position = 0
            $source.CopyTo($target)
        } finally { $algorithm.Dispose(); $target.Dispose(); $source.Dispose() }
        $manifest.Add(@{ path = $relative; bytes = $length; sha256 = $hash })
    }
    $metadata = @{ schema = 1; created = (Get-Date).ToUniversalTime().ToString('o'); levelName = $levelName; worldFolders = $worldFolders; files = @($manifest.ToArray()) }
    $entry = $archive.CreateEntry('backup-manifest.json')
    $writer = New-Object IO.StreamWriter($entry.Open(), (New-Object Text.UTF8Encoding($false)))
    try { $writer.Write(($metadata | ConvertTo-Json -Depth 6)) } finally { $writer.Dispose() }
} finally { $archive.Dispose(); $output.Dispose() }
[IO.File]::Move($temporaryPath, $archivePath)
Write-Output $archivePath
Write-Output "Respaldo completo: $($manifest.Count) archivos; incluye mundo, cuentas, permisos, mods y configuracion."
