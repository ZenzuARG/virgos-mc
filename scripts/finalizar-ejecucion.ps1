param([Parameter(Mandatory=$true)][string]$RunStarted,[int]$ExitCode=0,[ValidateSet('auto','manual')][string]$BackupLabel='auto')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'archivos.ps1')
$policy=Get-Content -LiteralPath (Join-Path $root 'config/virgos/maintenance.json') -Raw | ConvertFrom-Json
$requestPath=Join-Path $root '.runtime/checkpoint-request.json'
$restart=$false
if(Test-Path -LiteralPath $requestPath) {
    $request=Get-Content -LiteralPath $requestPath -Raw | ConvertFrom-Json
    $when=[DateTimeOffset]::Parse($request.requestedAt)
    $restart=($request.schema -eq 1 -and $request.reason -eq 'full-backup' -and $when -ge [DateTimeOffset]::Parse($RunStarted) -and $when -le [DateTimeOffset]::UtcNow -and ([DateTimeOffset]::UtcNow-$when).TotalMinutes -lt 15)
    if($restart -and $request.label -eq 'manual') {$BackupLabel='manual'}
}
if($ExitCode -ne 0) { throw 'El servidor termino con error. No se reinicia ni se trata ese estado como una copia consistente.' }
$archivePath=$null
if($policy.backupOnCleanStop -or $restart -or $BackupLabel -eq 'manual') {
    $result=@(& (Join-Path $PSScriptRoot 'respaldo.ps1') -Label $BackupLabel)
    $archivePath=[string]$result[0]
    if(-not (Test-Path -LiteralPath $archivePath)) { throw 'No se encontro el respaldo terminado.' }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive=[IO.Compression.ZipFile]::OpenRead($archivePath)
    $verified=$false
    try {
        $entry=$archive.GetEntry('backup-manifest.json')
        $reader=New-Object IO.StreamReader($entry.Open())
        try { $manifest=$reader.ReadToEnd() | ConvertFrom-Json } finally { $reader.Dispose() }
        if($manifest.worldFolders.Count -lt 6) { throw 'La copia completa no incluye las seis carpetas de mundos.' }
        foreach($file in $manifest.files) {
            $entry=$archive.GetEntry($file.path)
            if(-not $entry -or $entry.Length -ne $file.bytes) { throw "Respaldo incompleto: $($file.path)" }
            $hash=[Security.Cryptography.SHA256]::Create();$stream=$entry.Open()
            try { $actual=[BitConverter]::ToString($hash.ComputeHash($stream)).Replace('-','').ToLowerInvariant() } finally { $stream.Dispose();$hash.Dispose() }
            if($actual -ne $file.sha256) { throw "Respaldo corrupto: $($file.path)" }
        }
        $verified=$true
    } finally {
        $archive.Dispose()
        if(-not $verified) {
            $quarantine=Join-Path $root 'backups/unverified'
            [void][IO.Directory]::CreateDirectory($quarantine)
            Move-Item -LiteralPath $archivePath -Destination (Join-Path $quarantine ([IO.Path]::GetFileName($archivePath)))
        }
    }
    $record=@{completed=[DateTime]::UtcNow.ToString('o');archive=$archivePath;sha256=(Get-VerifiedHash -Path $archivePath);worldFolders=$manifest.worldFolders;verifiedFiles=$manifest.files.Count}
    $record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $root '.runtime/last-backup.json') -Encoding UTF8
    # Retention keeps two verified automatic snapshots and one latest manual/upgrade snapshot.
    $backupRoot=[IO.Path]::GetFullPath((Join-Path $root 'backups/full'))
    $automatic=@(Get-ChildItem -LiteralPath $backupRoot -File -Filter 'virgos-*-auto.zip' | Where-Object {$_.Name -match '^virgos-\d{8}-\d{6}-auto\.zip$'} | Sort-Object LastWriteTime -Descending)
    $total=($automatic | Measure-Object Length -Sum).Sum
    $keep=[Math]::Max(2,[int]$policy.retentionCount);$limit=[double]$policy.maxBackupGiB*1GB
    for($i=$automatic.Count-1;$i -ge 2;$i--) {
        if($i -lt $keep -and $total -le $limit) { break }
        $candidate=[IO.Path]::GetFullPath($automatic[$i].FullName)
        if([IO.Path]::GetDirectoryName($candidate) -ne $backupRoot -or $candidate -eq $archivePath) { throw 'Ruta de retencion invalida.' }
        $total-=$automatic[$i].Length
        Remove-Item -LiteralPath $candidate
    }
    $manual=@(Get-ChildItem -LiteralPath $backupRoot -File -Filter 'virgos-*.zip' |
        Where-Object {$_.Name -match '^virgos-\d{8}-\d{6}-(?!auto\.)(?:[A-Za-z0-9_-]+)\.zip$'} |
        Sort-Object LastWriteTime -Descending)
    $manualKeep=[Math]::Max(0,[int]$policy.manualRetentionCount)
    for($i=$manual.Count-1;$i -ge $manualKeep;$i--) {
        $candidate=[IO.Path]::GetFullPath($manual[$i].FullName)
        if([IO.Path]::GetDirectoryName($candidate) -ne $backupRoot) { throw 'Ruta de retencion manual invalida.' }
        Remove-Item -LiteralPath $candidate
    }
}
if(Test-Path -LiteralPath $requestPath) {
    Move-Item -LiteralPath $requestPath -Destination (Join-Path $root ('.runtime/checkpoint-completed-'+[Guid]::NewGuid().ToString('N')+'.json'))
}
@{restart=$restart;backup=$archivePath} | ConvertTo-Json -Compress
