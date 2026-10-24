$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
. (Join-Path $root 'templates\installer-common.ps1')
. (Join-Path $root 'templates\tlauncher-settings.ps1')
function Assert-TLauncherClosed {} # Fixture-only: never inspect real launcher processes.
# Every path belongs to this external fixture; no launcher discovery or UI runs.
$scratch=Join-Path ([IO.Path]::GetTempPath()) ('virgos-client-memory-'+[Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($scratch)
Write-Host ('SCRATCH='+$scratch)
$checks=New-Object Collections.Generic.List[string]
$failures=New-Object Collections.Generic.List[string]
function Assert($Condition,$Message) { if(-not $Condition) { throw $Message } }
function Check($Name,[scriptblock]$Body) {
    try { & $Body; $checks.Add($Name); Write-Host ('PASS '+$Name) }
    catch { $failures.Add($Name+': '+$_.Exception.Message); Write-Host ('FAIL '+$Name+': '+$_.Exception.Message) }
}
function Memory-Assignment([string]$Path,[string]$Variable) {
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseFile($Path,[ref]$tokens,[ref]$errors)
    if($errors.Count) { throw 'Fixture source does not parse.' }
    return @($ast.FindAll({param($n) $n -is [Management.Automation.Language.AssignmentStatementAst] -and $n.Left -is [Management.Automation.Language.VariableExpressionAst] -and $n.Left.VariablePath.UserPath -eq $Variable},$true))[0]
}
Check 'Fresh assistant chooses 8192 MiB' {
    $assignment=Memory-Assignment (Join-Path $root 'templates\asistente.ps1') 'script:memoryMb'
    $value=& ([scriptblock]::Create($assignment.Right.Extent.Text))
    Assert ($value -eq 8192) 'Fresh allocation must be 8192.'
}
Check 'Legacy installer requests normalize during repair' {
    $assignment=Memory-Assignment (Join-Path $root 'templates\install-launcher.ps1') 'memory'
    foreach($old in @(4096,5120,6144,8192)) {
        $request=[pscustomobject]@{memoryMb=$old}
        $actual=& ([scriptblock]::Create($assignment.Extent.Text+'; $memory'))
        Assert ($actual -eq 8192) ('Legacy request retained '+$actual)
    }
}
Check 'Persisted preferences migrate only memory and preserve unrelated fields' {
    $path=Join-Path $scratch 'preferencias.json'
    foreach($old in @(5120,6144,8192)) {
        Write-JsonAtomic $path @{memoryMb=$old;launcher='Oficial';installRoot='D:\Fixture';custom=@{keep='yes'}}
        $script:prefsPath=$path
        $assignment=Memory-Assignment (Join-Path $root 'templates\asistente.ps1') 'prefs'
        $prefs=& ([scriptblock]::Create($assignment.Right.Extent.Text))
        $stored=Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
        Assert ($prefs.memoryMb -eq 8192 -and $stored.memoryMb -eq 8192) 'Old preference was not migrated.'
        Assert ($stored.launcher -eq 'Oficial' -and $stored.installRoot -eq 'D:\Fixture' -and $stored.custom.keep -eq 'yes') 'Unrelated preferences changed.'
    }
    Assert (@(Get-ChildItem -LiteralPath $scratch -Filter 'preferencias.json.memoria-*.bak').Count -eq 2) 'Legacy preference backups missing or repeated for current preferences.'
    $request=@{launcher='TLauncher';memoryMb=5120;installRoot='D:\New fixture'}
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $root 'templates\asistente.ps1'),[ref]$tokens,[ref]$errors)
    $save=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.CommandAst] -and $n.GetCommandName() -eq 'Save-VirgosClientPreferences'},$true))
    Assert ($save.Count -eq 1) 'Assistant install action must preserve preference metadata.'
    & ([scriptblock]::Create($save[0].Extent.Text))
    $stored=Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
    Assert ($stored.memoryMb -eq 8192 -and $stored.launcher -eq 'TLauncher' -and $stored.custom.keep -eq 'yes') 'Install action lost unrelated preference metadata.'
}
Check 'Official profile fresh and repair use 8192 without touching other profiles' {
    $path=Join-Path $scratch 'launcher_profiles.json'
    Write-JsonAtomic $path @{profiles=@{other=@{name='Unrelated';javaArgs='-Xmx3G'}};selectedProfile='other';custom='keep'}
    foreach($iteration in @(1,2)) {
        Set-VirgosProfile $path 'D:\Fixture\Game' 'D:\Fixture\java.exe' 8192
        $stored=Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
        Assert ($stored.profiles.'virgos-mc-1.20.1'.javaArgs -match '-Xmx8192M') 'Official profile allocation differs.'
        Assert ($stored.profiles.other.javaArgs -eq '-Xmx3G' -and $stored.selectedProfile -eq 'other' -and $stored.custom -eq 'keep') 'Unrelated profile changed.'
    }
    Assert (@(Get-ChildItem -LiteralPath $scratch -Filter 'launcher_profiles.json*.bak').Count -ge 1) 'Profile backup missing.'
}
Check 'TLauncher fresh and repair allocate 8192 and restore original settings' {
    $path=Join-Path $scratch 'tlauncher-2.0.properties';$backup=Join-Path $scratch 'backups'
    $original="# TLauncher configuration file`r`nsettings.version=3`r`nminecraft.gamedir=C:\\Original`r`nminecraft.memory.ram2=3072`r`nlocale=es_ES`r`nunknown=keep`r`n"
    [IO.File]::WriteAllText($path,$original,$script:Utf8)
    foreach($iteration in @(1,2)) {
        [void](Set-VirgosTLauncher $path 'D:\Fixture\Game' 8192 $backup)
        $text=[IO.File]::ReadAllText($path)
        Assert ((Get-TLProperty $text 'minecraft.memory.ram2') -eq '8192' -and (Get-TLProperty $text 'minecraft.memory.ram3') -eq '8192') 'TLauncher allocation differs.'
        Assert ((Get-TLProperty $text 'unknown') -eq 'keep' -and (Get-TLProperty $text 'locale') -eq 'es_ES') 'Unrelated TLauncher settings changed.'
    }
    Restore-VirgosTLauncher $backup
    $restored=[IO.File]::ReadAllText($path)
    Assert ((Get-TLProperty $restored 'minecraft.memory.ram2') -eq '3072' -and $null -eq (Get-TLProperty $restored 'minecraft.memory.ram3')) 'Original RAM keys not restored.'
}
Check 'Distribution invokes both launcher setters with normalized legacy allocation' {
    $tokens=$null;$errors=$null
    $source=Join-Path $root 'templates\install-launcher.ps1'
    $ast=[Management.Automation.Language.Parser]::ParseFile($source,[ref]$tokens,[ref]$errors)
    $calls=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.CommandAst] -and $n.GetCommandName() -in @('Set-VirgosProfile','Set-VirgosTLauncher')},$true))
    Assert ($calls.Count -eq 2) 'Expected both actual distribution setter calls.'
    $request=[pscustomobject]@{memoryMb=5120}
    $assignment=Memory-Assignment $source 'memory'
    $memory=& ([scriptblock]::Create($assignment.Extent.Text+'; $memory'))
    $base=Join-Path $scratch 'distribution';[void][IO.Directory]::CreateDirectory($base)
    $game=Join-Path $base 'juego';$javaw=Join-Path $base 'javaw.exe'
    $path=Join-Path $base 'launcher_profiles.json';Write-JsonAtomic $path @{profiles=@{}}
    $tlConfig=Join-Path $base 'tlauncher-2.0.properties'
    [IO.File]::WriteAllText($tlConfig,"# TLauncher configuration file`r`nsettings.version=3`r`nminecraft.gamedir=C:\\Fixture`r`n",$script:Utf8)
    foreach($call in $calls) { & ([scriptblock]::Create($call.Extent.Text)) | Out-Null }
    $stored=Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
    Assert ($stored.profiles.'virgos-mc-1.20.1'.javaArgs -match '-Xmx8192M') 'Distribution official call did not allocate 8192.'
    Assert ((Get-TLProperty ([IO.File]::ReadAllText($tlConfig)) 'minecraft.memory.ram2') -eq '8192') 'Distribution TLauncher call did not allocate 8192.'
}
Check 'Invalid allocation is rejected before profile/settings writes' {
    foreach($invalid in @(0,4095,8193,-1)) {
        $path=Join-Path $scratch ('invalid-'+$invalid+'.json')
        $caught=$false;try { Set-VirgosProfile $path 'D:\Fixture' 'D:\java.exe' $invalid } catch { $caught=$true }
        Assert ($caught -and -not [IO.File]::Exists($path)) 'Invalid official allocation mutated a profile.'
        $caught=$false;try { Resolve-VirgosClientMemoryMb $invalid | Out-Null } catch { $caught=$true }
        Assert $caught 'Invalid installer request accepted.'
        $tlRoot=Join-Path $scratch ('invalid-tl-'+$invalid);[void][IO.Directory]::CreateDirectory($tlRoot)
        $tl=Join-Path $tlRoot 'tlauncher-2.0.properties';[IO.File]::WriteAllText($tl,'fixture sentinel')
        $caught=$false;try { Set-VirgosTLauncher $tl 'D:\Fixture' $invalid (Join-Path $tlRoot 'backups') | Out-Null } catch { $caught=$true }
        Assert ($caught -and [IO.File]::ReadAllText($tl) -eq 'fixture sentinel' -and -not [IO.Directory]::Exists((Join-Path $tlRoot 'backups'))) 'Invalid allocation modified TLauncher or created a backup.'
    }
}
Check 'Explicit low-level legacy allocations remain supported' {
    foreach($legacy in @(4096,5120,6144)) {
        $base=Join-Path $scratch ('legacy-'+$legacy);[void][IO.Directory]::CreateDirectory($base)
        $profile=Join-Path $base 'launcher_profiles.json'
        Set-VirgosProfile $profile 'D:\Fixture' 'D:\java.exe' $legacy
        $stored=Get-Content -LiteralPath $profile -Raw -Encoding UTF8 | ConvertFrom-Json
        Assert ($stored.profiles.'virgos-mc-1.20.1'.javaArgs.Contains('-Xmx'+$legacy+'M')) 'Explicit legacy profile allocation changed.'
        $tl=Join-Path $base 'tlauncher-2.0.properties'
        [IO.File]::WriteAllText($tl,"# TLauncher configuration file`r`nsettings.version=3`r`nminecraft.gamedir=C:\\Fixture`r`n",$script:Utf8)
        [void](Set-VirgosTLauncher $tl 'D:\Fixture' $legacy (Join-Path $base 'backup'))
        Assert ((Get-TLProperty ([IO.File]::ReadAllText($tl)) 'minecraft.memory.ram2') -eq [string]$legacy) 'Explicit legacy TLauncher allocation changed.'
    }
}
Write-JsonAtomic (Join-Path $scratch 'result.json') @{passed=($failures.Count -eq 0);checks=$checks.ToArray();failures=$failures.ToArray();scratch=$scratch}
if($failures.Count) { throw ($failures.Count.ToString()+' memory checks failed.') }
Write-Host ($checks.Count.ToString()+' client memory checks passed.')
