# Keep the pinned compatibility patch installed; retain current personal rendering settings.
function Get-VirgosDhSettingsPlan([string]$ConfigPath,[string]$DefaultPath) {
    foreach($candidate in @($ConfigPath,$DefaultPath)) {
        $cursor=[IO.Path]::GetFullPath($candidate)
        while($cursor) {
            if(Test-Path -LiteralPath $cursor) {
                if((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                    throw 'La configuración de DH no puede usar enlaces.'
                }
            }
            $cursor=[IO.Path]::GetDirectoryName($cursor)
        }
    }
    $seed=[IO.File]::ReadAllText($DefaultPath)
    if(([regex]::Matches($seed,'(?m)^_version\s*=\s*5\s*$')).Count -ne 1) { throw 'Configuración predeterminada de DH no válida.' }
    $original=if([IO.File]::Exists($ConfigPath)){[IO.File]::ReadAllText($ConfigPath)}else{''}
    # This installer edits only the canonical form emitted by DH, not general TOML.
    # Reject legal alternative spellings instead of appending duplicate logical keys.
    foreach($line in ($original -split '\r?\n')) {
        $content=$line.Trim()
        if(-not $content -or $content.StartsWith('#')) { continue }
        if($content.StartsWith('[')) {
            if($content -notmatch '^\[(?:[A-Za-z0-9_-]+\.)*[A-Za-z0-9_-]+\]\s*(?:#.*)?$') {
                throw 'Formato de tabla de DH no compatible; se conserva sin cambios.'
            }
            continue
        }
        $separator=$content.IndexOf('=')
        if($separator -lt 1 -or $content.Substring(0,$separator).Trim() -notmatch '^[A-Za-z0-9_-]+$') {
            throw 'Formato de clave de DH no compatible; se conserva sin cambios.'
        }
        $key=$content.Substring(0,$separator).Trim()
        $value=$content.Substring($separator+1).TrimStart()
        if($key -in @('client','advanced','autoUpdater') -or $value.StartsWith('{') -or
           $value.StartsWith('"""') -or $value.StartsWith(("'"*3))) {
            throw 'Formato compuesto de DH no compatible; se conserva sin cambios.'
        }
    }
    $versions=[regex]::Matches($original,'(?m)^\s*_version\s*=\s*([0-9]+)\s*(?:#.*)?$')
    if($versions.Count -gt 1) { throw 'La configuración de DH tiene versiones duplicadas.' }
    $version=if($versions.Count){[int]$versions[0].Groups[1].Value}else{0}
    if($version -gt 5) { throw 'La configuración de DH pertenece a una versión posterior; se conserva sin cambios.' }
    $text=$original
    if($version -lt 5) {
        # Upstream DH 3.3.3 resets pre-v5 settings too; retain the original in a backup.
        $text=$seed
    } else {
        $newline=if($text.Contains("`r`n")){"`r`n"}else{"`n"}
        $lines=New-Object Collections.Generic.List[string]
        foreach($line in ($text -split '\r?\n')) { $lines.Add($line) }
        $headers=@(for($i=0;$i -lt $lines.Count;$i++) {
            if($lines[$i] -match '^\s*\[client\.advanced\.autoUpdater\]\s*(?:#.*)?$') { $i }
        })
        if($headers.Count -gt 1) { throw 'La configuración de actualización de DH está duplicada.' }
        if(-not $headers.Count) {
            if($lines.Count -and $lines[$lines.Count-1] -ne '') { $lines.Add('') }
            $lines.Add('[client.advanced.autoUpdater]')
            $lines.Add('enableAutoUpdater = false')
            $lines.Add('')
        } else {
            $start=$headers[0]+1; $end=$lines.Count
            for($i=$start;$i -lt $lines.Count;$i++) {
                if($lines[$i] -match '^\s*\[') { $end=$i; break }
            }
            $keys=@(for($i=$start;$i -lt $end;$i++) { if($lines[$i] -match '^\s*enableAutoUpdater\s*=') { $i } })
            if($keys.Count -gt 1) { throw 'La opción de actualización de DH está duplicada.' }
            if($keys.Count) {
                $match=[regex]::Match($lines[$keys[0]],'^(\s*enableAutoUpdater\s*=\s*)(true|false)(\s*(?:#.*)?)$')
                if(-not $match.Success) { throw 'La opción de actualización de DH no es válida.' }
                $lines[$keys[0]]=$match.Groups[1].Value+'false'+$match.Groups[3].Value
            } else { $lines.Insert($end,'enableAutoUpdater = false') }
        }
        $text=$lines -join $newline
    }
    return [pscustomobject]@{ConfigPath=$ConfigPath;OriginalText=$original;Text=$text}
}

function Write-VirgosDhSettingsPlan($Plan) {
    if($Plan.Text -ceq $Plan.OriginalText) { return }
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Plan.ConfigPath))
    if($Plan.OriginalText) {
        Write-TextAtomic ($Plan.ConfigPath+'.virgos-'+[Guid]::NewGuid().ToString('N')+'.bak') $Plan.OriginalText
    }
    Write-TextAtomic $Plan.ConfigPath $Plan.Text
}
