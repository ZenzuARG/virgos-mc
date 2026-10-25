$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
. (Join-Path $root 'templates\client-keybindings.ps1')
$policy=Get-Content -LiteralPath (Join-Path $root 'pack\keybindings.json') -Raw | ConvertFrom-Json
function Assert($Condition,[string]$Message) { if(-not $Condition) { throw $Message } }

$fresh=Merge-VirgosKeyBindings "renderDistance:7`nkey_key.forward:key.keyboard.w`n" $policy
Assert ($fresh.Text.Contains('key_key.virgos_codex.open:key.keyboard.j')) 'Missing independent Codex key is assigned'
$custom=Merge-VirgosKeyBindings "renderDistance:7`nkey_key.heracles.open_quests:key.keyboard.u`nkey_iris.keybind.reload:key.keyboard.f12`n" $policy
Assert ($custom.Text.Contains('key_key.virgos_codex.open:key.keyboard.u')) 'Legacy personal Codex key transfers to independent action'
Assert ($custom.Text.Contains('key_key.heracles.open_quests:key.keyboard.unknown')) 'Redundant legacy action is unbound'
Assert ($custom.Text.Contains('key_iris.keybind.reload:key.keyboard.f12')) 'Personal shader binding survives'
Assert ($custom.Text.Contains('renderDistance:7')) 'Unrelated settings survive'
$unbound=Merge-VirgosKeyBindings "key_key.virgos_codex.open:key.keyboard.unknown`nkey_iris.keybind.reload:key.keyboard.r`n" $policy
Assert ($unbound.Text.Contains('key_key.virgos_codex.open:key.keyboard.j')) 'Unbound Codex is repaired'
Assert ($unbound.Text.Contains('key_iris.keybind.reload:key.keyboard.f8')) 'Old shader reload moves off spell-wheel key'
$disabled=Merge-VirgosKeyBindings "key_iris.keybind.reload:key.keyboard.unknown`n" $policy
Assert ($disabled.Text.Contains('key_iris.keybind.reload:key.keyboard.unknown')) 'Deliberately disabled shader action survives'
$explicit=Merge-VirgosKeyBindings "key_key.virgos_codex.open:key.keyboard.k`nkey_key.heracles.open_quests:key.keyboard.u`n" $policy
Assert ($explicit.Text.Contains('key_key.virgos_codex.open:key.keyboard.k')) 'Explicit independent custom binding wins'
Assert (@($explicit.Conflicts).Count -gt 0) 'Residual personal key conflicts are reported'
Assert ((Merge-VirgosKeyBindings $custom.Text $policy).Text -ceq $custom.Text) 'Repair is idempotent'
Assert ($fresh.Text.Contains('key_key.forward:key.keyboard.w')) 'Vanilla movement is preserved'
$duplicate=$false
try { Merge-VirgosKeyBindings "key_key.virgos_codex.open:key.keyboard.j`nkey_key.virgos_codex.open:key.keyboard.k`n" $policy | Out-Null } catch { $duplicate=$true }
Assert $duplicate 'Duplicate options are rejected without a write'
. (Join-Path $root 'templates\installer-common.ps1')
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('virgos-controls-'+[Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($fixture)
$optionsPath=Join-Path $fixture 'options.txt'
[IO.File]::WriteAllText($optionsPath,"renderDistance:7`nkey_key.virgos_codex.open:key.keyboard.k`n")
Set-VirgosKeyBindings $optionsPath (Join-Path $root 'pack\keybindings.json')
Assert ([IO.File]::ReadAllText($optionsPath).Contains('renderDistance:7')) 'Atomic adapter preserves unrelated settings'
$report=Get-Content -LiteralPath (Join-Path $fixture 'virgos-keybinding-conflicts.json') -Raw | ConvertFrom-Json
Assert (@($report.conflicts).Count -gt 0) 'Residual personal conflicts are written to the report'
$bad="key_key.virgos_codex.open:key.keyboard.j`nkey_key.virgos_codex.open:key.keyboard.k`n"
[IO.File]::WriteAllText($optionsPath,$bad)
$rejected=$false
try { Set-VirgosKeyBindings $optionsPath (Join-Path $root 'pack\keybindings.json') } catch { $rejected=$true }
Assert ($rejected -and [IO.File]::ReadAllText($optionsPath) -ceq $bad) 'Rejected duplicate options remain byte-for-byte unchanged'
foreach($case in @('missing-policy','duplicate-controls','unknown-schema','invalid-policy-json')) {
    $package=Join-Path $fixture $case
    $game=Join-Path $package 'instance'
    foreach($directory in @('bundled','overrides','instance\mods')) {
        [void][IO.Directory]::CreateDirectory((Join-Path $package $directory))
    }
    foreach($name in @('installer-common.ps1','client-keybindings.ps1','instalar-cliente.ps1')) {
        Copy-Item -LiteralPath (Join-Path $root ('templates\'+$name)) -Destination (Join-Path $package $name)
    }
    if($case -ne 'missing-policy') {
        $policyText=[IO.File]::ReadAllText((Join-Path $root 'pack\keybindings.json'))
        if($case -eq 'unknown-schema') { $policyText=$policyText.Replace('"schema": 1','"schema": 2') }
        if($case -eq 'invalid-policy-json') { $policyText='{' }
        [IO.File]::WriteAllText((Join-Path $package 'keybindings.json'),$policyText)
    }
    $jarName='virgos_codex-2.0.0.jar'
    $installed=Join-Path $game ('mods\'+$jarName)
    $included=Join-Path $package ('bundled\'+$jarName)
    [IO.File]::WriteAllText($installed,'previous verified installed codex')
    [IO.File]::WriteAllText($included,'new synthetic codex fixture')
    $old=@{version='2.0.0';minecraft='1.20.1';forge='47.4.22';files=@(@{filename=$jarName;sha512=(Get-FileDigest $installed);optional=$false;project='virgos-codex';bundled=$true})}
    $next=@{version='2.0.0';minecraft='1.20.1';forge='47.4.22';files=@(@{filename=$jarName;sha512=(Get-FileDigest $included);optional=$false;project='virgos-codex';bundled=$true})}
    $installedLock=Join-Path $game 'virgos-cliente.lock.json'
    $installedOptions=Join-Path $game 'options.txt'
    Write-JsonAtomic $installedLock $old
    Write-JsonAtomic (Join-Path $package 'cliente.lock.json') $next
    $saved="renderDistance:7`nkey_key.virgos_codex.open:key.keyboard.j`n"
    if($case -eq 'duplicate-controls') { $saved+="key_key.virgos_codex.open:key.keyboard.k`n" }
    [IO.File]::WriteAllText($installedOptions,$saved)
    $beforeJar=Get-FileDigest $installed
    $beforeLock=Get-FileDigest $installedLock
    $beforeOptions=Get-FileDigest $installedOptions
    $rejected=$false
    try { & (Join-Path $package 'instalar-cliente.ps1') -Destino $game } catch { $rejected=$true }
    Assert $rejected ($case+': public installer rejects the invalid controls input')
    Assert ((Get-FileDigest $installed) -eq $beforeJar) ($case+': installed Codex jar is unchanged after rejection')
    Assert ((Get-FileDigest $installedLock) -eq $beforeLock) ($case+': installed lock manifest is unchanged after rejection')
    Assert ((Get-FileDigest $installedOptions) -eq $beforeOptions) ($case+': saved controls are unchanged after rejection')
    Assert (-not [IO.Directory]::Exists((Join-Path $game '.virgos-update'))) ($case+': rejection does not create a staging directory')
}
Write-Output ('Controls fixture retained: '+$fixture)
Write-Output 'Client keybindings: missing/unbound repair, legacy transfer, custom preservation, conflicts and idempotency passed'
