function Get-VirgosSurfaceMapTarget([string]$Instance) {
    $relative = 'xaero/world-map/Multiplayer_virgos-mc.playit.plus/null/cm$virgos_surface_20261117'
    $target = [IO.Path]::GetFullPath((Join-Path $Instance $relative))
    for ($path = $target; $path; $path = [IO.Path]::GetDirectoryName($path)) {
        $item = Get-Item -Force -LiteralPath $path -ErrorAction SilentlyContinue
        if ($item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw 'No se puede importar el mapa en una ruta con enlaces.'
        }
        if ($item -and $path -ne $target -and -not $item.PSIsContainer) {
            throw 'La carpeta destinada al mapa no es válida.'
        }
    }
    return $target
}

function Install-VirgosSurfaceMap([string]$Instance, [string]$Archive) {
    $target = Get-VirgosSurfaceMapTarget $Instance
    if (Test-Path -LiteralPath $target) { return }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [IO.Compression.ZipFile]::OpenRead($Archive)
    $stage = $null
    try {
        $seen = @{}
        foreach ($entry in $zip.Entries) {
            if ($entry.FullName -cnotmatch '^cm\$converted/(-?[0-9]+_-?[0-9]+\.zip)\z' -or $seen.ContainsKey($entry.Name)) {
                throw 'El paquete contiene archivos de mapa inesperados.'
            }
            $seen[$entry.Name] = $true
        }
        if (-not $seen.Count) { throw 'El paquete del mapa está vacío.' }
        $parent = [IO.Path]::GetDirectoryName($target)
        [void][IO.Directory]::CreateDirectory($parent)
        $stage = Join-Path $parent ('.virgos-surface-' + [Guid]::NewGuid().ToString('N'))
        [void][IO.Directory]::CreateDirectory($stage)
        foreach ($entry in $zip.Entries) {
            [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, (Join-Path $stage $entry.Name), $false)
        }
        # Directory.Move never replaces an existing map, including a concurrent import.
        [void](Get-VirgosSurfaceMapTarget $Instance)
        if (-not (Test-Path -LiteralPath $target)) {
            [IO.Directory]::Move($stage, $target)
            $stage = $null
        }
    } finally {
        $zip.Dispose()
        if ($stage -and [IO.Directory]::Exists($stage)) {
            [void](Get-VirgosSurfaceMapTarget $Instance)
            $stagedItem = Get-Item -Force -LiteralPath $stage -ErrorAction Stop
            if ($stagedItem.Parent.FullName -ne $parent -or
                ($stagedItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                throw 'Ruta temporal del mapa no válida.'
            }
            Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction Stop
        }
    }
}
