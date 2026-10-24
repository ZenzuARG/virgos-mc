param([string]$Package = (Join-Path $PSScriptRoot '..\.lab\installer-v2\package'))
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$package=[IO.Path]::GetFullPath($Package)
. (Join-Path $package 'asistente\installer-common.ps1')
. (Join-Path $package 'asistente\tlauncher-settings.ps1')
$script:StatusPath=$null
$testRoot=Join-Path ([IO.Path]::GetTempPath()) ('virgos-installer-unit-'+[Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($testRoot)
$checks=New-Object Collections.Generic.List[string]
function Assert($Condition,$Message) { if(-not $Condition) { throw $Message }; $checks.Add($Message) }
$tlFixture=Join-Path $testRoot 'tlauncher-2.0.properties'
[IO.File]::WriteAllText($tlFixture,"# TLauncher configuration file`r`nsettings.version=3`r`nminecraft.gamedir=C:\Existing Games\Minecraft`r`n")
Assert ((Read-TLauncherSettings $tlFixture) -match 'settings.version=3') 'TLauncher without RAM keys is accepted'
$tlBackup=Join-Path $testRoot 'tl-backup'
[void](Set-VirgosTLauncher $tlFixture 'D:\Games with spaces\Virgos-MC\juego' 5120 $tlBackup)
$tlText=[IO.File]::ReadAllText($tlFixture)
Assert ($tlText -match '(?m)^minecraft\.memory\.ram2=5120\r?$' -and $tlText -match '(?m)^minecraft\.memory\.ram3=5120\r?$') 'Missing TLauncher RAM keys are created and verified'
$profile=Join-Path $testRoot 'launcher_profiles.json'
$original=@{profiles=@{forge=@{name='Other pack';lastVersionId='1.20.1-forge-47.4.26';gameDir='C:\Existing Games\Other';javaArgs='-Xmx8G'};vanilla=@{name='Vanilla';lastVersionId='1.21.1'}};settings=@{enableHistorical=$true};selectedProfile='vanilla';arbitrary=@{keep='yes'}}
Write-JsonAtomic $profile $original
$before=Get-Content -LiteralPath $profile -Raw | ConvertFrom-Json
Set-VirgosProfile $profile 'D:\Games with spaces\Virgos-MC\juego' 'D:\Games with spaces\javaw.exe' 5120
$after=Get-Content -LiteralPath $profile -Raw | ConvertFrom-Json
Assert (($before.profiles.forge | ConvertTo-Json -Compress) -eq ($after.profiles.forge | ConvertTo-Json -Compress)) 'Existing Forge profile unchanged'
Assert (($before.profiles.vanilla | ConvertTo-Json -Compress) -eq ($after.profiles.vanilla | ConvertTo-Json -Compress)) 'Existing vanilla profile unchanged'
Assert ($after.selectedProfile -eq 'vanilla' -and $after.settings.enableHistorical -and $after.arbitrary.keep -eq 'yes') 'Other launcher metadata preserved'
Assert ($after.profiles.'virgos-mc-1.20.1'.javaArgs -match '-Xmx5120M' -and $after.profiles.'virgos-mc-1.20.1'.lastVersionId -eq '1.20.1-forge-47.4.22') 'New profile uses exact Forge and RAM'
Assert (@(Get-ChildItem -LiteralPath $testRoot -Filter '*.bak').Count -eq 1) 'Profile backup created'
Set-VirgosProfile $profile 'D:\Games with spaces\Virgos-MC\juego' 'D:\Games with spaces\javaw.exe' 6144
$after=Get-Content -LiteralPath $profile -Raw | ConvertFrom-Json
Assert (@($after.profiles.PSObject.Properties).Count -eq 3 -and $after.profiles.'virgos-mc-1.20.1'.javaArgs -match '6144M') 'Repeat installation updates one profile without duplicates'
$bad=Join-Path $testRoot 'bad.json'; [IO.File]::WriteAllText($bad,'{invalid')
$caught=$false; try { Set-VirgosProfile $bad 'D:\Game' 'D:\java.exe' 5120 } catch { $caught=$true }
Assert ($caught -and [IO.File]::ReadAllText($bad) -eq '{invalid') 'Malformed profiles rejected without replacement'
$caught=$false; try { Get-VerifiedDownload 'http://example.com/a.jar' (Join-Path $testRoot 'bad.jar') 'x' } catch { $caught=$true }
Assert ($caught -and -not [IO.File]::Exists((Join-Path $testRoot 'bad.jar'))) 'Untrusted download URL rejected'
$mods=Join-Path $testRoot 'unknown\mods'; [void][IO.Directory]::CreateDirectory($mods)
[IO.File]::WriteAllText((Join-Path $mods 'alien.jar'),'do not remove')
$caught=$false; try { & (Join-Path $package 'asistente\instalar-cliente.ps1') -Destino (Join-Path $testRoot 'unknown') } catch { $caught=$true }
Assert ($caught -and [IO.File]::ReadAllText((Join-Path $mods 'alien.jar')) -eq 'do not remove') 'Foreign mods block installation and remain intact'
$tiny=Join-Path $testRoot 'tiny'; [void][IO.Directory]::CreateDirectory((Join-Path $tiny 'overrides'))
foreach($name in @('installer-common.ps1','instalar-cliente.ps1')) { Copy-Item -LiteralPath (Join-Path $package ('asistente\'+$name)) -Destination (Join-Path $tiny $name) }
$payload=Join-Path $tiny 'payload'; [IO.File]::WriteAllText($payload,'test payload')
$manifest=@{minecraft='1.20.1';forge='47.4.22';files=@(@{filename='fixture.jar';url='https://cdn.modrinth.com/fixture.jar';sha512=(Get-FileDigest $payload);optional=$false;project='Fixture'})}
Write-JsonAtomic (Join-Path $tiny 'cliente.lock.json') $manifest
$instance=Join-Path $tiny 'instance'; [void][IO.Directory]::CreateDirectory((Join-Path $instance 'mods'))
Copy-Item -LiteralPath $payload -Destination (Join-Path $instance 'mods\fixture.jar')
foreach($name in @('servers.dat','options.txt')) {
    [IO.File]::WriteAllText((Join-Path $tiny ('overrides\'+$name)),'package defaults')
    [IO.File]::WriteAllText((Join-Path $instance $name),'player data')
}
& (Join-Path $tiny 'instalar-cliente.ps1') -Destino $instance
Assert ([IO.File]::ReadAllText((Join-Path $instance 'servers.dat')) -eq 'player data') 'Repair preserves existing server list'
Assert ([IO.File]::ReadAllText((Join-Path $instance 'options.txt')) -eq 'player data') 'Repair preserves player controls and settings'
$manifest.version='0.2.0-rc1'; Write-JsonAtomic (Join-Path $tiny 'cliente.lock.json') $manifest
[IO.File]::WriteAllText((Join-Path $instance 'options.txt'),"renderDistance:7`nkey_key.push_to_talk:key.keyboard.left.alt`n")
$voiceDir=Join-Path $instance 'config\voicechat'; [void][IO.Directory]::CreateDirectory($voiceDir)
[IO.File]::WriteAllText((Join-Path $voiceDir 'voicechat-client.properties'),'microphone=Existing device')
$voiceOverride=Join-Path $tiny 'overrides\config\voicechat'; [void][IO.Directory]::CreateDirectory($voiceOverride)
[IO.File]::WriteAllText((Join-Path $voiceOverride 'voicechat-client.properties'),'microphone=')
& (Join-Path $tiny 'instalar-cliente.ps1') -Destino $instance
$options=[IO.File]::ReadAllText((Join-Path $instance 'options.txt'))
Assert ($options.Contains('renderDistance:7') -and $options.Contains('key_key.push_to_talk:key.keyboard.left.alt') -and $options.Contains('key_key.voice_chat:key.keyboard.o')) 'Voice upgrade adds only missing controls'
Assert ([IO.File]::ReadAllText((Join-Path $voiceDir 'voicechat-client.properties')) -eq 'microphone=Existing device') 'Voice repair preserves selected microphone'
[IO.File]::WriteAllText((Join-Path $instance 'mods\fixture.jar'),'corrupt')
$caught=$false; try { & (Join-Path $tiny 'instalar-cliente.ps1') -Destino $instance -Verificar } catch { $caught=$true }
Assert $caught 'Verification detects corrupt mod content'
Copy-Item -LiteralPath $payload -Destination (Join-Path $instance 'mods\fixture.jar') -Force
$optional=Join-Path $instance 'mods\optional.jar';[IO.File]::WriteAllText($optional,'optional payload')
$optionalEntry=@{filename='optional.jar';url='https://cdn.modrinth.com/optional.jar';sha512=(Get-FileDigest $optional);optional=$true;project='Optional fixture'}
$manifest.files=@($manifest.files[0],$optionalEntry);Write-JsonAtomic (Join-Path $tiny 'cliente.lock.json') $manifest
[IO.File]::WriteAllText($optional,'corrupt optional')
$caught=$false;try { & (Join-Path $tiny 'instalar-cliente.ps1') -Destino $instance -Verificar } catch { $caught=$true }
Assert $caught 'Already installed optional mods are verified even without optional selection'
[IO.File]::WriteAllText($optional,'optional payload')
$manifest.files=@($manifest.files[0],$optionalEntry,$optionalEntry);Write-JsonAtomic (Join-Path $tiny 'cliente.lock.json') $manifest
$caught=$false;try { & (Join-Path $tiny 'instalar-cliente.ps1') -Destino $instance -Verificar } catch { $caught=$true }
Assert $caught 'Duplicate current manifest entries rejected'
$manifest.files=@($manifest.files[0],$optionalEntry);Write-JsonAtomic (Join-Path $tiny 'cliente.lock.json') $manifest
# Upgrade removes only a hash-matching file recorded by the previous release.
Copy-Item -LiteralPath $payload -Destination (Join-Path $instance 'mods\fixture.jar') -Force
$oldFile=Join-Path $instance 'mods\fixture-old.jar'; [IO.File]::WriteAllText($oldFile,'previous release')
$oldManifest=@{minecraft='1.20.1';forge='47.4.22';files=@(@{filename='fixture-old.jar';sha512=(Get-FileDigest $oldFile)})}
Write-JsonAtomic (Join-Path $instance 'virgos-cliente.lock.json') $oldManifest
$caught=$false; try { & (Join-Path $tiny 'instalar-cliente.ps1') -Destino $instance -Verificar } catch { $caught=$true }
Assert ($caught -and [IO.File]::Exists($oldFile)) 'Verification reports obsolete release without changing it'
& (Join-Path $tiny 'instalar-cliente.ps1') -Destino $instance
$retained=@(Get-ChildItem -LiteralPath (Join-Path $instance 'respaldos-actualizacion') -Recurse -File -Filter 'fixture-old.jar')
Assert (-not [IO.File]::Exists($oldFile) -and $retained.Count -eq 1 -and [IO.File]::ReadAllText($retained[0].FullName) -eq 'previous release') 'Managed obsolete mod moved to recovery backup'
Assert ([IO.File]::ReadAllText((Join-Path $instance 'mods\fixture.jar')) -eq 'test payload') 'Current release survives managed migration'
[IO.File]::WriteAllText($oldFile,'modified previous mod')
Write-JsonAtomic (Join-Path $instance 'virgos-cliente.lock.json') $oldManifest
$caught=$false; try { & (Join-Path $tiny 'instalar-cliente.ps1') -Destino $instance } catch { $caught=$true }
Assert ($caught -and [IO.File]::ReadAllText($oldFile) -eq 'modified previous mod') 'Modified obsolete mod rejected and preserved'
$oldManifest.files[0].filename='../escape.jar'; Write-JsonAtomic (Join-Path $instance 'virgos-cliente.lock.json') $oldManifest
$caught=$false; try { Get-ManagedUpgradePlan $instance $manifest } catch { $caught=$true }
Assert $caught 'Traversal in previous release manifest rejected'
$manifest.files[0].filename='../escape.jar'; Write-JsonAtomic (Join-Path $tiny 'cliente.lock.json') $manifest
$caught=$false; try { & (Join-Path $tiny 'instalar-cliente.ps1') -Destino $instance } catch { $caught=$true }
Assert $caught 'Path traversal in manifest rejected'
# Embedded UI ships without a remote URL, but is checked before any migration.
$embedded=Join-Path $testRoot 'embedded';[void][IO.Directory]::CreateDirectory((Join-Path $embedded 'bundled'));[void][IO.Directory]::CreateDirectory((Join-Path $embedded 'overrides'))
foreach($name in @('installer-common.ps1','instalar-cliente.ps1')) { Copy-Item -LiteralPath (Join-Path $package ('asistente\'+$name)) -Destination (Join-Path $embedded $name) }
$jar=Join-Path $embedded 'bundled\virgos_codex-2.0.0.jar';[IO.File]::WriteAllText($jar,'verified embedded UI fixture')
$embeddedManifest=@{version='2.0.0';minecraft='1.20.1';forge='47.4.22';files=@(@{filename='virgos_codex-2.0.0.jar';project='virgos-codex';bundled=$true;optional=$false;sha512=(Get-FileDigest $jar)})}
Write-JsonAtomic (Join-Path $embedded 'cliente.lock.json') $embeddedManifest
$game=Join-Path $embedded 'game'
& (Join-Path $embedded 'instalar-cliente.ps1') -Destino $game
Assert ((Get-FileDigest (Join-Path $game 'mods\virgos_codex-2.0.0.jar')) -eq $embeddedManifest.files[0].sha512) 'Bundled codex installed and hashed without network URL'
& (Join-Path $embedded 'instalar-cliente.ps1') -Destino $game -Verificar
[IO.File]::WriteAllText($jar,'corrupted UI fixture')
$caught=$false;try { & (Join-Path $embedded 'instalar-cliente.ps1') -Destino $game } catch { $caught=$true }
Assert ($caught -and (Get-FileDigest (Join-Path $game 'mods\virgos_codex-2.0.0.jar')) -eq $embeddedManifest.files[0].sha512) 'Corrupt bundled payload rejected before replacing installed UI'
$embeddedManifest.files[0].filename='virgos_codex-9.0.0.jar';Write-JsonAtomic (Join-Path $embedded 'cliente.lock.json') $embeddedManifest
$caught=$false;try { & (Join-Path $embedded 'instalar-cliente.ps1') -Destino $game } catch { $caught=$true }
Assert $caught 'Missing bundled component rejected before migration'
$embeddedManifest.files[0].filename='../escape.jar';Write-JsonAtomic (Join-Path $embedded 'cliente.lock.json') $embeddedManifest
$caught=$false;try { & (Join-Path $embedded 'instalar-cliente.ps1') -Destino $game } catch { $caught=$true }
Assert $caught 'Bundled path traversal rejected'
$report=@{passed=$true;powershell=$PSVersionTable.PSVersion.ToString();checks=$checks.ToArray();testDirectory=$testRoot;utc=[DateTime]::UtcNow.ToString('o')}
Write-JsonAtomic (Join-Path $testRoot 'installer-v3-unit.json') $report
$report | ConvertTo-Json -Depth 5
