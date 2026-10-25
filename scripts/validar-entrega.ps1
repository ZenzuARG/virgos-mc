param([string]$ServerPath=(Split-Path -Parent $PSScriptRoot),[switch]$Quiet)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'archivos.ps1')
$root=[IO.Path]::GetFullPath($ServerPath)
function Read-Lock([string]$Relative) { Get-Content -LiteralPath (Join-Path $root $Relative) -Raw -Encoding UTF8 | ConvertFrom-Json }
$base=Read-Lock 'versions.lock.json'
$expected=New-Object Collections.Generic.List[object]
$expected.Add(@{folder='.';file='ketting-server.jar';algorithm=$base.launcher.algorithm;hash=$base.launcher.hash})
$expected.Add(@{folder='mods';file=$base.playitCompanion.file;algorithm=$base.playitCompanion.algorithm;hash=$base.playitCompanion.hash})
$expected.Add(@{folder='plugins';file=$base.authMe.file;algorithm=$base.authMe.algorithm;hash=$base.authMe.hash})
foreach($lockPath in @('pack/mods.lock.json','pack/custom-artifacts.lock.json')) {
    foreach($item in (Read-Lock $lockPath).artifacts) {
        if($item.sides -contains 'server' -and $item.mode -ne 'optional') {
            $expected.Add(@{folder='mods';file=$item.filename;algorithm=$item.hash_algorithm;hash=$item.hash;size=$item.size})
        }
    }
}
$lp=Read-Lock 'pack/luckperms.lock.json'
$expected.Add(@{folder='plugins';file=$lp.filename;algorithm='SHA512';hash=$lp.sha512})
foreach($item in (Read-Lock 'pack/administration.lock.json')) {
    $expected.Add(@{folder='plugins';file=$item.filename;algorithm=$item.hash_algorithm;hash=$item.hash})
}
$serverLockPath=Join-Path $root 'pack/server-artifacts.lock.json'
if(Test-Path -LiteralPath $serverLockPath) {
    $serverLock=Read-Lock 'pack/server-artifacts.lock.json'
    if($serverLock.schema -ne 1 -or $null -eq $serverLock.artifacts) { throw 'Manifiesto de overrides del servidor invalido.' }
    $overridden=@{}
    foreach($override in $serverLock.artifacts) {
        $filename=[string]$override.filename
        if([IO.Path]::GetFileName($filename) -ne $filename -or $filename -notmatch '^[A-Za-z0-9_.+ ()-]+\.jar$') { throw 'Nombre de override del servidor invalido.' }
        if($overridden.ContainsKey($filename)) { throw "Override de servidor duplicado: $filename" }
        $overridden[$filename]=$true
        $matches=@($expected | Where-Object { $_.folder -eq 'mods' -and $_.file -ceq $filename })
        if($matches.Count -ne 1) { throw "Override de servidor sin componente base unico: $filename" }
        $component=$matches[0]
        if($null -eq $component.size -or $null -eq $override.base_size -or $override.base_hash_algorithm -ine $component.algorithm -or $override.base_hash -cne $component.hash -or [long]$override.base_size -ne [long]$component.size) { throw "La referencia base del override no coincide: $filename" }
        if([string]::IsNullOrWhiteSpace([string]$override.reason)) { throw "Falta el motivo del override de servidor: $filename" }
        $algorithm=[string]$override.hash_algorithm
        $hash=[string]$override.hash
        $expectedHashLength=if($algorithm -ieq 'sha256'){64}elseif($algorithm -ieq 'sha512'){128}else{0}
        if($expectedHashLength -eq 0 -or $hash -notmatch "^[A-Fa-f0-9]{$expectedHashLength}$" -or [long]$override.size -le 0) { throw "Hash o tamaño de override invalido: $filename" }
        $component.algorithm=$algorithm
        $component.hash=$hash
        $component.size=[long]$override.size
    }
}
$seen=@{}
foreach($item in $expected) {
    if([IO.Path]::GetFileName($item.file) -ne $item.file -or $item.file -notmatch '^[A-Za-z0-9_.+ ()-]+\.jar$' -or $item.file -match 'virgos_local_qa') { throw 'Nombre de componente invalido en el manifiesto.' }
    $relative=$item.folder+'/'+$item.file
    if($seen.ContainsKey($relative)) { throw "Componente duplicado: $relative" }
    $seen[$relative]=$true
    $path=Join-Path $root $relative
    if(-not (Test-Path -LiteralPath $path)) { throw "Falta el componente: $relative" }
    if((Get-VerifiedHash -Path $path -Algorithm $item.algorithm) -ne $item.hash) { throw "Componente modificado o incompleto: $relative" }
}
foreach($folder in @('mods','plugins')) {
    foreach($file in Get-ChildItem -LiteralPath (Join-Path $root $folder) -Filter '*.jar' -File) {
        if(-not $seen.ContainsKey($folder+'/'+$file.Name)) { throw "JAR no incluido en la entrega: $folder/$($file.Name). Conservado sin iniciar el servidor." }
    }
}
$java=Join-Path $root ('.runtime/'+$base.java.folder+'/bin/java.exe')
if(-not (Test-Path -LiteralPath $java)) { throw 'Falta Java portable. Ejecuta preparar.bat.' }
if(-not (Select-String -LiteralPath (Join-Path $root 'eula.txt') -Pattern '^\s*eula\s*=\s*true\s*$' -Quiet)) { throw 'Falta la aceptacion del EULA.' }
if(-not $Quiet) { @{result='OK';components=$expected.Count;mods=@($expected | Where-Object {$_.folder -eq 'mods'}).Count;plugins=@($expected | Where-Object {$_.folder -eq 'plugins'}).Count} | ConvertTo-Json -Compress }
