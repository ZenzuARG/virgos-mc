param([Parameter(Mandatory=$true)][string]$Package)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$package=[IO.Path]::GetFullPath($Package)
if($package -eq $root -or $package.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Use an external fixture package, never the worktree.' }
. (Join-Path $package 'asistente\installer-common.ps1')
. (Join-Path $package 'asistente\tlauncher-settings.ps1')
function Assert-TLauncherClosed {} # Fixture-only: never inspect actual launcher processes.
$script:StatusPath=$null
$testRoot=Join-Path ([IO.Path]::GetTempPath()) ('virgos-installer-unit-'+[Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($testRoot)
Write-Host ('SCRATCH='+$testRoot)
$checks=New-Object Collections.Generic.List[string]
function Assert($Condition,$Message) { if(-not $Condition) { throw $Message }; $checks.Add($Message) }
$tlFixture=Join-Path $testRoot 'tlauncher-2.0.properties'
[IO.File]::WriteAllText($tlFixture,"# TLauncher configuration file`r`nsettings.version=3`r`nminecraft.gamedir=C:\Existing Games\Minecraft`r`n")
Assert ((Read-TLauncherSettings $tlFixture) -match 'settings.version=3') 'TLauncher without RAM keys is accepted'
$tlBackup=Join-Path $testRoot 'tl-backup'
[void](Set-VirgosTLauncher $tlFixture 'D:\Games with spaces\Virgos-MC\juego' 8192 $tlBackup)
$tlText=[IO.File]::ReadAllText($tlFixture)
Assert ($tlText -match '(?m)^minecraft\.memory\.ram2=8192\r?$' -and $tlText -match '(?m)^minecraft\.memory\.ram3=8192\r?$') 'Missing TLauncher RAM keys are created at eight GiB and verified'
$profile=Join-Path $testRoot 'launcher_profiles.json'
$original=@{profiles=@{forge=@{name='Other pack';lastVersionId='1.20.1-forge-47.4.26';gameDir='C:\Existing Games\Other';javaArgs='-Xmx8G'};vanilla=@{name='Vanilla';lastVersionId='1.21.1'}};settings=@{enableHistorical=$true};selectedProfile='vanilla';arbitrary=@{keep='yes'}}
Write-JsonAtomic $profile $original
$before=Get-Content -LiteralPath $profile -Raw | ConvertFrom-Json
Set-VirgosProfile $profile 'D:\Games with spaces\Virgos-MC\juego' 'D:\Games with spaces\javaw.exe' 8192
$after=Get-Content -LiteralPath $profile -Raw | ConvertFrom-Json
Assert (($before.profiles.forge | ConvertTo-Json -Compress) -eq ($after.profiles.forge | ConvertTo-Json -Compress)) 'Existing Forge profile unchanged'
Assert (($before.profiles.vanilla | ConvertTo-Json -Compress) -eq ($after.profiles.vanilla | ConvertTo-Json -Compress)) 'Existing vanilla profile unchanged'
Assert ($after.selectedProfile -eq 'vanilla' -and $after.settings.enableHistorical -and $after.arbitrary.keep -eq 'yes') 'Other launcher metadata preserved'
Assert ($after.profiles.'virgos-mc-1.20.1'.javaArgs -match '-Xmx8192M' -and $after.profiles.'virgos-mc-1.20.1'.lastVersionId -eq '1.20.1-forge-47.4.22') 'New profile uses exact Forge and eight GiB'
Assert (@(Get-ChildItem -LiteralPath $testRoot -Filter '*.bak').Count -eq 1) 'Profile backup created'
Set-VirgosProfile $profile 'D:\Games with spaces\Virgos-MC\juego' 'D:\Games with spaces\javaw.exe' 8192
$after=Get-Content -LiteralPath $profile -Raw | ConvertFrom-Json
Assert (@($after.profiles.PSObject.Properties).Count -eq 3 -and $after.profiles.'virgos-mc-1.20.1'.javaArgs -match '8192M') 'Repeat installation retains eight GiB without duplicate profiles'
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
# This intentionally models an older package with neither controls helper nor policy.
foreach($name in @('installer-common.ps1','instalar-cliente.ps1')) {
    $source=Join-Path $package ('asistente\'+$name)
    if(Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination (Join-Path $tiny $name) }
}
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
foreach($name in @('installer-common.ps1','instalar-cliente.ps1','client-keybindings.ps1')) {
    $source=Join-Path $package ('asistente\'+$name)
    if(Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination (Join-Path $embedded $name) }
}
$embeddedPolicy=Join-Path $package 'asistente\keybindings.json'
if(Test-Path -LiteralPath $embeddedPolicy) { Copy-Item -LiteralPath $embeddedPolicy -Destination (Join-Path $embedded 'keybindings.json') }
$dhHelper=Join-Path $package 'asistente\dh-client-settings.ps1'
$dhSeed=Join-Path $package 'asistente\overrides\config\DistantHorizons.toml'
if((Test-Path -LiteralPath $dhHelper) -and (Test-Path -LiteralPath $dhSeed)) {
    Copy-Item -LiteralPath $dhHelper -Destination (Join-Path $embedded 'dh-client-settings.ps1')
    [void][IO.Directory]::CreateDirectory((Join-Path $embedded 'overrides\config'))
    Copy-Item -LiteralPath $dhSeed -Destination (Join-Path $embedded 'overrides\config\DistantHorizons.toml')
}
$jar=Join-Path $embedded 'bundled\virgos_codex-2.0.0.jar';[IO.File]::WriteAllText($jar,'verified embedded UI fixture')
$embeddedManifest=@{version='2.0.0';minecraft='1.20.1';forge='47.4.22';files=@(@{filename='virgos_codex-2.0.0.jar';project='virgos-codex';bundled=$true;optional=$false;sha512=(Get-FileDigest $jar)})}
Write-JsonAtomic (Join-Path $embedded 'cliente.lock.json') $embeddedManifest
$game=Join-Path $embedded 'game'
& (Join-Path $embedded 'instalar-cliente.ps1') -Destino $game
Assert ((Get-FileDigest (Join-Path $game 'mods\virgos_codex-2.0.0.jar')) -eq $embeddedManifest.files[0].sha512) 'Bundled codex installed and hashed without network URL'
& (Join-Path $embedded 'instalar-cliente.ps1') -Destino $game -Verificar
# All candidate roles remain local bundled inputs; neither DH component needs a URL.
$codexEntry=$embeddedManifest.files[0]
foreach($role in @(
    @{filename='DistantHorizons-3.3.3-1.20.1-fabric-forge.jar';project='distant-horizons'},
    @{filename='virgos_dh_compat-0.1.0.jar';project='virgos-dh-compat'}
)) {
    $included=Join-Path $embedded ('bundled\'+$role.filename)
    [IO.File]::WriteAllText($included,'verified local '+$role.project)
    $embeddedManifest.files+=@{filename=$role.filename;project=$role.project;bundled=$true;optional=$false;sha512=(Get-FileDigest $included)}
}
Write-JsonAtomic (Join-Path $embedded 'cliente.lock.json') $embeddedManifest
& (Join-Path $embedded 'instalar-cliente.ps1') -Destino $game
foreach($entry in $embeddedManifest.files) {
    Assert ((Get-FileDigest (Join-Path $game ('mods\'+$entry.filename))) -eq $entry.sha512) ('Known bundled role installed without network: '+$entry.project)
}
if(Test-Path -LiteralPath (Join-Path $embedded 'dh-client-settings.ps1')) {
    $config=Join-Path $game 'config\DistantHorizons.toml'
    [IO.File]::WriteAllText($config,"_version = 5`n[client.advanced.graphics.quality]`nlodChunkRenderDistanceRadius = 77`n[client.advanced.autoUpdater]`nenableAutoUpdater = true`n")
    & (Join-Path $embedded 'instalar-cliente.ps1') -Destino $game
    $text=[IO.File]::ReadAllText($config)
    Assert ($text.Contains('lodChunkRenderDistanceRadius = 77') -and $text.Contains('enableAutoUpdater = false')) 'DH settings plan preserves personal radius and pins auto-updater'
    $lock=Join-Path $game 'virgos-cliente.lock.json';$lockBefore=[IO.File]::ReadAllBytes($lock)
    $mod=Join-Path $game 'mods\virgos_codex-2.0.0.jar';$modBefore=Get-FileDigest $mod
    [IO.File]::WriteAllText($config,"_version = 6`n")
    $caught=$false;try { & (Join-Path $embedded 'instalar-cliente.ps1') -Destino $game } catch { $caught=$true }
    Assert ($caught -and (Get-FileDigest $mod) -eq $modBefore -and [Convert]::ToBase64String([IO.File]::ReadAllBytes($lock)) -eq [Convert]::ToBase64String($lockBefore) -and [IO.File]::ReadAllText($config) -eq "_version = 6`n") 'Invalid future DH config rejected before mod or lock mutation'
    [IO.File]::WriteAllText($config,$text)
    $helper=Join-Path $embedded 'dh-client-settings.ps1';$held=$helper+'.held'
    [IO.File]::Move($helper,$held)
    try {
        $caught=$false;try { & (Join-Path $embedded 'instalar-cliente.ps1') -Destino $game } catch { $caught=$true }
        Assert ($caught -and (Get-FileDigest $mod) -eq $modBefore -and [IO.File]::ReadAllText($config) -eq $text) 'Incomplete DH helper/seed pair rejected before mutation'
    } finally { [IO.File]::Move($held,$helper) }
}
foreach($invalidRole in @(
    @{filename='virgos_local_qa-0.1.0.jar';project='virgos-codex'},
    @{filename='DistantHorizons-3.3.4-1.20.1-fabric-forge.jar';project='distant-horizons'},
    @{filename='virgos_dh_compat-0.1.0.jar';project='unexpected'}
)) {
    $invalidJar=Join-Path $embedded ('bundled\'+$invalidRole.filename);[IO.File]::WriteAllText($invalidJar,'invalid role fixture')
    $embeddedManifest.files=@(@{filename=$invalidRole.filename;project=$invalidRole.project;bundled=$true;optional=$false;sha512=(Get-FileDigest $invalidJar)})
    Write-JsonAtomic (Join-Path $embedded 'cliente.lock.json') $embeddedManifest
    $caught=$false;try { & (Join-Path $embedded 'instalar-cliente.ps1') -Destino $game } catch { $caught=$true }
    Assert $caught ('Unexpected bundled role rejected: '+$invalidRole.filename)
}
$embeddedManifest.files=@($codexEntry);Write-JsonAtomic (Join-Path $embedded 'cliente.lock.json') $embeddedManifest
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
