param(
    [Parameter(Mandatory=$true)][string]$ArchivePath,
    [Parameter(Mandatory=$true)][string]$RestoreTo
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'archivos.ps1')
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$destination = [IO.Path]::GetFullPath($RestoreTo)
if (-not $destination.StartsWith($projectRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'El destino debe estar dentro del proyecto.' }
if (Test-Path -LiteralPath $destination) { throw 'El destino ya existe. La restauracion nunca sobrescribe archivos.' }
$archive = [IO.Compression.ZipFile]::OpenRead([IO.Path]::GetFullPath($ArchivePath))
try {
    $entry = $archive.GetEntry('backup-manifest.json')
    if (-not $entry) { throw 'Falta el manifiesto del respaldo.' }
    $reader = New-Object IO.StreamReader($entry.Open())
    try { $manifest = $reader.ReadToEnd() | ConvertFrom-Json } finally { $reader.Dispose() }
    if ($manifest.schema -ne 1 -or $manifest.files.Count -eq 0) { throw 'Manifiesto invalido.' }
    $paths = @{}
    foreach ($file in $manifest.files) {
        $path = [IO.Path]::GetFullPath((Join-Path $destination $file.path))
        if (-not $path.StartsWith($destination + '\', [StringComparison]::OrdinalIgnoreCase) -or $paths.ContainsKey($path)) { throw 'Ruta insegura o repetida en el respaldo.' }
        $paths[$path] = $true
        $entry = $archive.GetEntry($file.path)
        if (-not $entry -or $entry.Length -ne $file.bytes -or $file.sha256 -notmatch '^[a-f0-9]{64}$') { throw "Entrada invalida: $($file.path)" }
    }
    if ($archive.Entries.Count -ne $manifest.files.Count + 1) { throw 'Hay entradas fuera del manifiesto.' }
    [void][IO.Directory]::CreateDirectory($destination)
    foreach ($file in $manifest.files) {
        $path = [IO.Path]::GetFullPath((Join-Path $destination $file.path))
        [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path))
        $source = $archive.GetEntry($file.path).Open()
        $target = [IO.File]::Open($path, [IO.FileMode]::CreateNew)
        try { $source.CopyTo($target) } finally { $target.Dispose(); $source.Dispose() }
        if ((Get-VerifiedHash -Path $path) -ne $file.sha256) { throw "Hash incorrecto al restaurar $($file.path)" }
    }
    $report = @{ verifiedFiles = $manifest.files.Count; source = [IO.Path]::GetFullPath($ArchivePath); restoredTo = $destination; checked = (Get-Date).ToUniversalTime().ToString('o') }
    $report | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $destination 'restore-verification.json') -Encoding UTF8
    Write-Output "Restauracion comprobada: $($manifest.files.Count) archivos en $destination"
} finally { $archive.Dispose() }
