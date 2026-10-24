# Only launcher preferences are touched. Account and authentication files are never read.
function Assert-TLauncherClosed {
    $processes = Get-CimInstance Win32_Process -Filter "Name='java.exe' OR Name='javaw.exe' OR Name='TLauncher.exe'" -ErrorAction Stop
    if (@($processes | Where-Object { $_.Name -eq 'TLauncher.exe' -or ($_.CommandLine -and $_.CommandLine -match '(?i)org\.tlauncher\.|TLauncher[^"\r\n]*\.jar') }).Count) {
        throw 'Cierra TLauncher por completo antes de preparar o restaurar sus ajustes. No hace falta desinstalarlo.'
    }
}
function ConvertFrom-TLProperty([string]$Value) {
    return [regex]::Replace($Value, '\\(?:u[0-9a-fA-F]{4}|.)', [System.Text.RegularExpressions.MatchEvaluator]{ param($m)
        $v=$m.Value.Substring(1)
        if($v.StartsWith('u') -and $v.Length -eq 5) { return [string][char][Convert]::ToInt32($v.Substring(1),16) }
        switch($v) { 'n' {return "`n"} 'r' {return "`r"} 't' {return "`t"} 'f' {return [string][char]12} default {return $v} }
    })
}
function ConvertTo-TLProperty([string]$Value) {
    $s=$Value.Replace('\','\\').Replace("`r",'\r').Replace("`n",'\n').Replace("`t",'\t')
    if($s.StartsWith(' ')) { $s='\'+$s }
    return $s
}
function Get-TLProperty([string]$Text,[string]$Key) {
    $matches=[regex]::Matches($Text,'(?m)^[ \t]*'+[regex]::Escape($Key)+'[ \t]*[=:][ \t]*(.*)\r?$')
    if($matches.Count -gt 1) { throw "TLauncher tiene la opcion $Key duplicada. Conservamos el archivo para revision." }
    if($matches.Count -eq 0) { return $null }
    $value=$matches[0].Groups[1].Value.TrimEnd("`r")
    if($value -match '(?<!\\)(?:\\\\)*\\$') { throw 'TLauncher usa un ajuste dividido en varias lineas; se conserva para revision.' }
    return ConvertFrom-TLProperty $value
}
function Set-TLPropertyText([string]$Text,[string]$Key,$Value) {
    [void](Get-TLProperty $Text $Key)
    $pattern='(?m)^[ \t]*'+[regex]::Escape($Key)+'[ \t]*[=:][^\r\n]*(?:\r?\n|$)'
    if($null -eq $Value) { return [regex]::Replace($Text,$pattern,'') }
    $line=$Key+'='+(ConvertTo-TLProperty ([string]$Value))+"`r`n"
    if([regex]::IsMatch($Text,$pattern)) { return [regex]::Replace($Text,$pattern,[System.Text.RegularExpressions.MatchEvaluator]{param($m) $line}) }
    return $Text.TrimEnd("`r","`n")+"`r`n"+$line
}
function Read-TLauncherSettings([string]$Path) {
    if(-not [IO.File]::Exists($Path)) { throw 'Abri TLauncher una vez y cerralo. Luego toca Reintentar. Si es portable, elegi su archivo tlauncher-2.0.properties en Opciones.' }
    if([IO.Path]::GetFileName($Path) -ne 'tlauncher-2.0.properties' -or (Get-Item -LiteralPath $Path).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Elegi el archivo original tlauncher-2.0.properties, sin enlaces.' }
    $text=[IO.File]::ReadAllText($Path,(New-Object Text.UTF8Encoding($false,$true)))
    if($text -notmatch '(?m)^#\s*TLauncher configuration file' -or (Get-TLProperty $text 'settings.version') -ne '3') { throw 'La configuracion de TLauncher no es reconocida; no se modifico. Revisa la version y la carpeta en Opciones.' }
# Some TLauncher builds do not write the optional RAM keys until the first
# manual launch. We can safely add them later; only the game directory is
# required to identify a valid installation.
if($null -eq (Get-TLProperty $text 'minecraft.gamedir')) { throw 'Falta minecraft.gamedir en TLauncher. Abrilo una vez y cerra el launcher antes de reintentar.' }
    return $text
}
function Find-TLauncherSettingsPath {
    $candidates = @(
        (Join-Path $env:APPDATA '.tlauncher\tlauncher-2.0.properties'),
        (Join-Path $env:LOCALAPPDATA 'TLauncher\tlauncher-2.0.properties'),
        (Join-Path $env:APPDATA 'TLauncher\tlauncher-2.0.properties')
    )
    foreach($candidate in ($candidates | Select-Object -Unique)) {
        if([IO.File]::Exists($candidate)) { return [IO.Path]::GetFullPath($candidate) }
    }
    return [IO.Path]::GetFullPath((Join-Path $env:APPDATA '.tlauncher\tlauncher-2.0.properties'))
}
function Set-VirgosTLauncher([string]$Path,[string]$GameDir,[int]$MemoryMb,[string]$BackupRoot) {
    Assert-TLauncherClosed
    if($MemoryMb -lt 4096 -or $MemoryMb -gt 8192) { throw 'Memoria fuera del rango permitido.' }
    $path=[IO.Path]::GetFullPath($Path);$text=Read-TLauncherSettings $path
    $updates=[ordered]@{'minecraft.gamedir'=[IO.Path]::GetFullPath($GameDir);'minecraft.memory.ram2'=[string]$MemoryMb;'minecraft.memory.ram3'=[string]$MemoryMb;'login.version.game'='1.20.1-forge-47.4.22';'minecraft.versions.modified'='true';'minecraft.java.selected'='0';'modpack.combobox.index'='0'}
    $recordPath=Join-Path $BackupRoot 'tlauncher-ajustes.json'
    $original=[ordered]@{};foreach($key in $updates.Keys){$original[$key]=Get-TLProperty $text $key}
    if([IO.File]::Exists($recordPath)) {
        $record=Get-Content -LiteralPath $recordPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if($record.path -ne $path) { throw 'Ya existe un respaldo de otro TLauncher en esta carpeta. Usa otra carpeta de instalacion o restaura primero los ajustes anteriores.' }
        # Older installers did not manage minecraft.memory.ram3. Preserve its
        # current value before adding it to the managed settings on upgrade.
        foreach($key in $updates.Keys) {
            if(-not $record.original.PSObject.Properties[$key]) {
                $record.original | Add-Member -NotePropertyName $key -NotePropertyValue (Get-TLProperty $text $key)
            }
        }
    } else {
        [void][IO.Directory]::CreateDirectory($BackupRoot)
        $backup=Join-Path $BackupRoot ('tlauncher-'+[Guid]::NewGuid().ToString('N')+'.properties.bak')
        [IO.File]::WriteAllBytes($backup,[IO.File]::ReadAllBytes($path))
        $record=[pscustomobject]@{schema=1;path=$path;backup=$backup;original=$original;managed=$updates}
    }
    $changed=$text;foreach($key in $updates.Keys){$changed=Set-TLPropertyText $changed $key $updates[$key]}
    # Save recovery metadata before the mutation; a retry preserves the first original settings.
    $record.managed=$updates;Write-JsonAtomic $recordPath $record
    if([IO.File]::ReadAllText($path) -cne $text) { throw 'TLauncher cambio sus ajustes durante la instalacion. Cerralo y reintenta.' }
    if($changed -cne $text){Write-TextAtomic $path $changed}
    foreach($key in $updates.Keys){if((Get-TLProperty ([IO.File]::ReadAllText($path)) $key) -cne $updates[$key]){throw "No se pudo verificar el ajuste $key."}}
    return $recordPath
}
function Restore-VirgosTLauncher([string]$BackupRoot) {
    Assert-TLauncherClosed
    $recordPath=Join-Path $BackupRoot 'tlauncher-ajustes.json'
    if(-not [IO.File]::Exists($recordPath)){throw 'Todavia no hay ajustes de TLauncher respaldados para esta instalacion.'}
    $record=Get-Content -LiteralPath $recordPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if($record.schema -ne 1 -or -not [IO.File]::Exists($record.backup)){throw 'El respaldo de ajustes no es valido.'}
    $text=Read-TLauncherSettings $record.path;$changed=$text
    $keys=@('minecraft.gamedir','minecraft.memory.ram2','minecraft.memory.ram3','login.version.game','minecraft.versions.modified','minecraft.java.selected','modpack.combobox.index')
    foreach($key in $keys){
        if(-not $record.managed.PSObject.Properties[$key] -or -not $record.original.PSObject.Properties[$key]){throw 'Faltan opciones en el registro de recuperacion.'}
        $now=Get-TLProperty $text $key
        if($now -cne $record.managed.$key -and $now -cne $record.original.$key){throw "Cambiaste $key despues de instalar. Se conserva; revisa el respaldo antes de restaurar."}
        $changed=Set-TLPropertyText $changed $key $record.original.$key
    }
    if([IO.File]::ReadAllText($record.path) -cne $text){throw 'TLauncher cambio sus ajustes. Cerralo y reintenta.'}
    Write-TextAtomic $record.path $changed
}
