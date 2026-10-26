function Get-VirgosDhPathMetadata([string]$Path) {
    if(-not ('Virgos.DhPathMetadata' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
namespace Virgos {
    public sealed class DhPathMetadata {
        public uint Attributes;
        public uint Tag;
        [StructLayout(LayoutKind.Sequential)]
        private struct AttributeTagInfo { public uint Attributes; public uint Tag; }
        [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
        private static extern SafeFileHandle CreateFileW(string name, uint access, uint sharing,
            IntPtr security, uint creation, uint flags, IntPtr template);
        [DllImport("kernel32.dll", SetLastError=true)]
        private static extern bool GetFileInformationByHandleEx(SafeFileHandle handle, int infoClass,
            out AttributeTagInfo info, uint size);
        public static DhPathMetadata Read(string path) {
            // Query this entry itself, without following a junction or a dangling symlink.
            using(var handle=CreateFileW(path,0,7,IntPtr.Zero,3,0x02200000,IntPtr.Zero)) {
                if(handle.IsInvalid) {
                    int error=Marshal.GetLastWin32Error();
                    if(error==2 || error==3) return null;
                    throw new Win32Exception(error,"Cannot inspect DH path: "+path);
                }
                AttributeTagInfo info;
                if(!GetFileInformationByHandleEx(handle,9,out info,8))
                    throw new Win32Exception(Marshal.GetLastWin32Error(),"Cannot inspect DH path: "+path);
                return new DhPathMetadata { Attributes=info.Attributes,Tag=info.Tag };
            }
        }
        public static bool Allowed(uint attributes,uint tag) {
            if((attributes & 0x400u)==0) return true;
            // Only documented CloudFiles tags; unknown tags and name surrogates fail closed.
            return (tag & 0x20000000u)==0 && (tag & 0xFFFF0FFFu)==0x9000001Au;
        }
    }
}
'@
    }
    return [Virgos.DhPathMetadata]::Read($Path)
}

# Keep the pinned patch and migrate known pack defaults without replacing personal settings.
function Get-VirgosDhSettingsPlan([string]$ConfigPath,[string]$DefaultPath) {
    foreach($candidate in @($ConfigPath,$DefaultPath)) {
        $ancestors=New-Object Collections.Generic.List[string]
        $cursor=[IO.Path]::GetFullPath($candidate)
        while($cursor) {
            $ancestors.Add($cursor)
            $cursor=[IO.Path]::GetDirectoryName($cursor)
        }
        $ancestors.Reverse()
        foreach($entry in $ancestors) {
            $metadata=Get-VirgosDhPathMetadata $entry
            if($null -ne $metadata -and -not [Virgos.DhPathMetadata]::Allowed($metadata.Attributes,$metadata.Tag)) {
                throw ('La configuracion de DH no puede usar enlaces o redirecciones desconocidas: '+$entry+'. Extrae el ZIP y elige una carpeta local sin enlaces.')
            }
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
        # Old pack seeds restricted even remote cached requests to 512 blocks
        # around world origin. Let the server enforce its own generation boundary.
        # Only migrate the known defaults; customized values remain untouched.
        foreach($setting in @(
            @{Table='common.worldGenerator';Key='generationMaxChunkRadius';Replacement='0'},
            @{Table='client.advanced.graphics.quality';Key='lodChunkRenderDistanceRadius';Replacement='256'}
        )) {
            $tablePattern='^\s*\['+[regex]::Escape($setting.Table)+'\]\s*(?:#.*)?$'
            $headers=@(for($i=0;$i -lt $lines.Count;$i++) { if($lines[$i] -match $tablePattern) { $i } })
            if($headers.Count -gt 1) { throw 'La configuración de distancia de DH está duplicada.' }
            if(-not $headers.Count) { continue }
            $start=$headers[0]+1; $end=$lines.Count
            for($i=$start;$i -lt $lines.Count;$i++) {
                if($lines[$i] -match '^\s*\[') { $end=$i; break }
            }
            $keyPattern='^\s*'+[regex]::Escape($setting.Key)+'\s*='
            $keys=@(for($i=$start;$i -lt $end;$i++) { if($lines[$i] -match $keyPattern) { $i } })
            if($keys.Count -gt 1) { throw 'La opción de distancia de DH está duplicada.' }
            if(-not $keys.Count) { continue }
            $match=[regex]::Match($lines[$keys[0]],'^(\s*'+[regex]::Escape($setting.Key)+'\s*=\s*)([0-9]+)(\s*(?:#.*)?)$')
            if(-not $match.Success) { throw 'La opción de distancia de DH no es válida.' }
            if($match.Groups[2].Value -eq '32') {
                $lines[$keys[0]]=$match.Groups[1].Value+$setting.Replacement+$match.Groups[3].Value
            }
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
