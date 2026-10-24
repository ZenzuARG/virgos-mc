$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
. (Join-Path $root 'templates\installer-common.ps1')
. (Join-Path $root 'templates\tlauncher-settings.ps1')
$sandbox=Join-Path $root ('.lab\tlauncher-settings-'+[Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($sandbox)
$file=Join-Path $sandbox 'tlauncher-2.0.properties'
$backup=Join-Path $sandbox 'backup'
$checks=New-Object Collections.Generic.List[string]
function Assert($value,$label) { if(-not $value) { throw $label };$checks.Add($label) }
$original="# TLauncher configuration file`r`nsettings.version=3`r`nminecraft.gamedir=C:\\Juegos\\Mis mundos`r`nminecraft.memory.ram2=3072`r`nlogin.version.game=1.19.4`r`nminecraft.java.selected=17`r`nlocale=es_ES`r`nunknown.setting=keep\\:exact`r`n"
[IO.File]::WriteAllText($file,$original,$script:Utf8)
$game=Join-Path $sandbox 'Juegos de José\juego'
[void](Set-VirgosTLauncher $file $game 5120 $backup)
$changed=Read-TLauncherSettings $file
Assert ((Get-TLProperty $changed 'minecraft.gamedir') -ceq $game) 'Unicode and spaces in Windows path round trip'
Assert ((Get-TLProperty $changed 'login.version.game') -eq '1.20.1-forge-47.4.22') 'Pinned Forge selected'
Assert ((Get-TLProperty $changed 'minecraft.memory.ram2') -eq '5120') 'RAM configured'
Assert ((Get-TLProperty $changed 'minecraft.java.selected') -eq '0' -and (Get-TLProperty $changed 'modpack.combobox.index') -eq '0') 'Automatic Java and base version list selected'
Assert ($changed.Contains('unknown.setting=keep\\:exact') -and $changed.Contains('locale=es_ES')) 'Unmanaged settings preserved literally'
$record=Get-Content -LiteralPath (Join-Path $backup 'tlauncher-ajustes.json') -Raw -Encoding UTF8 | ConvertFrom-Json
Assert ([IO.File]::ReadAllText($record.backup) -ceq $original) 'Exact original backup retained'
[void](Set-VirgosTLauncher $file $game 6144 $backup)
$record=Get-Content -LiteralPath (Join-Path $backup 'tlauncher-ajustes.json') -Raw -Encoding UTF8 | ConvertFrom-Json
Assert ($record.original.'minecraft.memory.ram2' -eq '3072' -and $record.managed.'minecraft.memory.ram2' -eq '6144') 'Repair keeps first original and updates managed values'
$changed=Read-TLauncherSettings $file
[IO.File]::WriteAllText($file,$changed.Replace('locale=es_ES','locale=en_US'),$script:Utf8)
Restore-VirgosTLauncher $backup
$restored=Read-TLauncherSettings $file
Assert ((Get-TLProperty $restored 'minecraft.gamedir') -eq 'C:\Juegos\Mis mundos' -and (Get-TLProperty $restored 'minecraft.memory.ram2') -eq '3072') 'Original game directory and RAM restored'
Assert ($null -eq (Get-TLProperty $restored 'modpack.combobox.index')) 'Originally missing keys removed on restore'
Assert ($restored.Contains('locale=en_US')) 'Later unrelated preferences survive restoration'
Restore-VirgosTLauncher $backup
Assert ([IO.File]::ReadAllText($file) -ceq $restored) 'Restore is idempotent'
[void](Set-VirgosTLauncher $file $game 5120 $backup)
$changed=Read-TLauncherSettings $file
[IO.File]::WriteAllText($file,(Set-TLPropertyText $changed 'minecraft.memory.ram2' '4096'),$script:Utf8)
$before=[IO.File]::ReadAllText($file);$caught=$false
try { Restore-VirgosTLauncher $backup } catch { $caught=$true }
Assert ($caught -and [IO.File]::ReadAllText($file) -ceq $before) 'Manual managed-key edits block destructive restoration'
foreach($invalid in @(($original.Replace('settings.version=3','settings.version=99')),($original+"minecraft.gamedir=D:\\other`r`n"),($original.Replace('3072',"3072\`r`ncontinued")))) {
    [IO.File]::WriteAllText($file,$invalid,$script:Utf8);$caught=$false
    try { Set-VirgosTLauncher $file $game 5120 $backup | Out-Null } catch { $caught=$true }
    Assert ($caught -and [IO.File]::ReadAllText($file) -ceq $invalid) 'Unsupported, duplicate or multiline settings preserved on rejection'
}
Assert ((ConvertFrom-TLProperty 'Jos\u00e9\tA') -ceq "José`tA") 'Java unicode and tab escapes parsed'
# Leave a real patched fixture for the upstream Java Properties parser check.
[IO.File]::WriteAllText($file,$original,$script:Utf8)
[void](Set-VirgosTLauncher $file $game 5120 $backup)
Write-JsonAtomic (Join-Path $root '.lab\reports\tlauncher-settings-v4.json') @{passed=$true;powershell=$PSVersionTable.PSVersion.ToString();checks=$checks.ToArray();fixture=$file;expectedGameDir=$game}
Write-Host ($checks.Count.ToString()+' TLauncher settings checks passed.')
