$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'templates/installer-common.ps1')
. (Join-Path $root 'templates/dh-client-settings.ps1')
$scratch=Join-Path ([IO.Path]::GetTempPath()) ('virgos-dh-settings-'+[Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($scratch)
$seed=Join-Path $root 'pack/client-overrides/config/DistantHorizons.toml'
$path=Join-Path $scratch 'DistantHorizons.toml'
function Assert($Condition,$Message) { if(-not $Condition){throw $Message}; Write-Output ('PASS '+$Message) }
$plan=Get-VirgosDhSettingsPlan $path $seed
Assert (-not [IO.File]::Exists($path)) 'Fresh settings preflight does not write files'
Write-VirgosDhSettingsPlan $plan
$fresh=[IO.File]::ReadAllText($path)
Assert ($fresh -match 'lodChunkRenderDistanceRadius = 32' -and $fresh -match 'enableAutoUpdater = false') 'Fresh pinned DH settings use bounded radius and no self-update'
$custom="_version = 5`r`n[client.advanced.graphics.quality]`r`nlodChunkRenderDistanceRadius = 96`r`n[client.advanced.autoUpdater]`r`nenableAutoUpdater = true # personal comment`r`nenableSilentUpdates = false`r`n"
[IO.File]::WriteAllText($path,$custom)
$plan=Get-VirgosDhSettingsPlan $path $seed
Assert ([IO.File]::ReadAllText($path) -ceq $custom) 'Existing settings remain unchanged during preflight'
Write-VirgosDhSettingsPlan $plan
$changed=[IO.File]::ReadAllText($path)
Assert ($changed -ceq $custom.Replace('enableAutoUpdater = true','enableAutoUpdater = false')) 'Only the self-update flag changes in a current personal configuration'
$backups=@(Get-ChildItem -LiteralPath $scratch -Filter '*.bak')
Assert ($backups.Count -eq 1 -and [IO.File]::ReadAllText($backups[0].FullName) -ceq $custom) 'Original custom configuration is recoverable'
$plan=Get-VirgosDhSettingsPlan $path $seed
Write-VirgosDhSettingsPlan $plan
Assert (@(Get-ChildItem -LiteralPath $scratch -Filter '*.bak').Count -eq 1) 'Repeat settings application is idempotent'
$old="_version = 4`n[client]`nlegacy = true`n"
[IO.File]::WriteAllText($path,$old)
Write-VirgosDhSettingsPlan (Get-VirgosDhSettingsPlan $path $seed)
Assert ([IO.File]::ReadAllText($path) -ceq $fresh) 'Old native schema gets the new bounded seed after backup'
foreach($invalid in @("_version = 6`n", "_version = 5`n[client.advanced.autoUpdater]`nenableAutoUpdater = true`nenableAutoUpdater = false`n")) {
    [IO.File]::WriteAllText($path,$invalid)
    $rejected=$false
    try { [void](Get-VirgosDhSettingsPlan $path $seed) } catch { $rejected=$true }
    Assert ($rejected -and [IO.File]::ReadAllText($path) -ceq $invalid) 'Unsupported or ambiguous settings reject without mutation'
}
foreach($header in @('[client.advanced.autoUpdater ]','[client . advanced . autoUpdater]','["client"."advanced"."autoUpdater"]')) {
    $personal="_version = 5`n$header`nenableAutoUpdater = true`n"
    [IO.File]::WriteAllText($path,$personal)
    $rejected=$false
    try { [void](Get-VirgosDhSettingsPlan $path $seed) } catch { $rejected=$true }
    Assert ($rejected -and [IO.File]::ReadAllText($path) -ceq $personal) 'Alternative TOML table spelling rejects without changing personal settings'
}
$personal="_version = 5`n[client.advanced.autoUpdater]`n"+'"enableAutoUpdater" = true'+"`n"
[IO.File]::WriteAllText($path,$personal)
$rejected=$false
try { [void](Get-VirgosDhSettingsPlan $path $seed) } catch { $rejected=$true }
Assert ($rejected -and [IO.File]::ReadAllText($path) -ceq $personal) 'Quoted managed key rejects without writing an invalid duplicate'
Write-Output ('DH settings fixture retained: '+$scratch)
