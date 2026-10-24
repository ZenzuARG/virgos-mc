$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$javaBin = Join-Path $root '.runtime\jdk-17.0.20.1+1\bin'
$cache = Join-Path $root '.cache\gradle\caches\modules-2\files-2.1\org.ow2.asm'
$asm = (Get-ChildItem -LiteralPath (Join-Path $cache 'asm\9.9.1') -Recurse -Filter '*.jar' | Select-Object -First 1).FullName
$tree = (Get-ChildItem -LiteralPath (Join-Path $cache 'asm-tree\9.9.1') -Recurse -Filter '*.jar' | Select-Object -First 1).FullName
Push-Location $root
try {
    & (Join-Path $javaBin 'javac.exe') -cp "$asm;$tree" -d '.cache/v02/patch-classes' 'dev/playit-udp-fix/PatchCompanion.java'
    if ($LASTEXITCODE -ne 0) { throw 'Patch compilation failed' }
    & (Join-Path $javaBin 'java.exe') -cp "$asm;$tree;.cache/v02/patch-classes" PatchCompanion '.cache/playit_companion-forge-0.1.2.jar' 'pack/local/playit_companion-forge-0.1.2-virgos.1.jar'
    if ($LASTEXITCODE -ne 0) { throw 'Patch verification failed' }
} finally { Pop-Location }
