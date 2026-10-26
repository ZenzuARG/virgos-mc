$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'templates/dh-client-settings.ps1')
$scratch=Join-Path ([IO.Path]::GetTempPath()) ('virgos-dh-cloud-'+[Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($scratch)
$seed=Join-Path $scratch 'seed.toml'; $config=Join-Path $scratch 'settings.toml'
[IO.File]::WriteAllText($seed,"_version = 5`n")
[IO.File]::WriteAllText($config,"_version = 5`n")
$native=if(Get-Command Get-VirgosDhPathMetadata -ErrorAction SilentlyContinue){(Get-Command Get-VirgosDhPathMetadata).ScriptBlock}else{$null}
$script:fixturePath=$config; $script:fixtureTag=[Convert]::ToUInt32('9000001A',16)
$script:fixtureFailure=$false
function Get-Item {
    param([string]$LiteralPath,[switch]$Force)
    if($LiteralPath -eq $script:fixturePath){return [pscustomobject]@{Attributes=[IO.FileAttributes]::ReparsePoint}}
    Microsoft.PowerShell.Management\Get-Item -LiteralPath $LiteralPath -Force:$Force
}
function Get-VirgosDhPathMetadata([string]$Path) {
    if($Path -eq $script:fixturePath){
        if($script:fixtureFailure){throw 'Simulated metadata access denied'}
        return [pscustomobject]@{Attributes=[uint32]1024;Tag=$script:fixtureTag}
    }
    if($native){return & $native $Path}
    $item=Microsoft.PowerShell.Management\Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if($item){return [pscustomobject]@{Attributes=[uint32]$item.Attributes;Tag=[uint32]0}}
}
function Assert($Condition,$Message){if(-not $Condition){throw $Message};Write-Output ('PASS '+$Message)}
try {
    # Exercise the public planning boundary, not just a tag predicate.
    foreach($target in @($config,$seed,$scratch)){
        $script:fixturePath=$target
        for($index=0;$index -lt 16;$index++){
            $script:fixtureTag=[uint32]([Convert]::ToUInt32('9000001A',16)+$index*4096)
            $plan=Get-VirgosDhSettingsPlan $config $seed
            Assert ($plan.OriginalText -eq "_version = 5`n") ('Cloud metadata accepted for '+$target+' variant '+$index)
        }
        foreach($hex in @('A000000C','A0000003','20000001','80000021','80000017','00000000')){
            $script:fixtureTag=[Convert]::ToUInt32($hex,16)
            $rejected=$false;try{[void](Get-VirgosDhSettingsPlan $config $seed)}catch{$rejected=$true}
            Assert $rejected ('Unsafe or unknown tag rejected: '+$hex)
        }
        $script:fixtureFailure=$true
        $rejected=$false;try{[void](Get-VirgosDhSettingsPlan $config $seed)}catch{$rejected=$true}
        Assert $rejected 'Metadata failures reject without silently treating a path as absent'
        $script:fixtureFailure=$false
    }
    Assert (([IO.File]::ReadAllText($config) -eq "_version = 5`n") -and ([IO.File]::ReadAllText($seed) -eq "_version = 5`n") -and @(Get-ChildItem -LiteralPath $scratch).Count -eq 2) 'Planning and rejection preserve both files without backups or temporary output'
} finally {
    Remove-Item Function:\Get-Item
    if($native){Set-Item Function:\Get-VirgosDhPathMetadata $native}else{Remove-Item Function:\Get-VirgosDhPathMetadata}
}
if($native){
    $ordinary=Get-VirgosDhPathMetadata $config
    Assert (($ordinary.Attributes -band 1024) -eq 0) 'Native metadata query accepts an ordinary file'
    Assert ($null -eq (Get-VirgosDhPathMetadata (Join-Path $scratch 'absent.toml'))) 'Native query distinguishes a missing destination'
    $linked=Join-Path $scratch 'OneDrive'
    [void](New-Item -ItemType Junction -Path $linked -Target $scratch)
    $rejected=$false;try{[void](Get-VirgosDhSettingsPlan (Join-Path $linked 'settings.toml') $seed)}catch{$rejected=$true}
    Assert $rejected 'A real junction named OneDrive remains rejected'
}
Write-Output ('Cloud path fixture retained: '+$scratch)
