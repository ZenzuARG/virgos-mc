param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$pluginDirectory = Join-Path $Root 'plugins\TreeFeller'
$configPath = Join-Path $pluginDirectory 'config.yml'
$overridePath = Join-Path $Root 'pack\server-overrides\plugins\TreeFeller\config.yml'

New-Item -ItemType Directory -Path $pluginDirectory -Force | Out-Null

if (-not (Test-Path -LiteralPath $configPath)) {
    Copy-Item -LiteralPath $overridePath -Destination $configPath -Force
    Write-Output 'TreeFeller config created without unsupported COPPER_AXE.'
    exit 0
}

$lines = Get-Content -LiteralPath $configPath
$inTools = $false
$changed = $false
$filtered = foreach ($line in $lines) {
    if ($line -match '^tools:\s*$') {
        $inTools = $true
    } elseif ($inTools -and $line -match '^\S' -and $line -notmatch '^\s*#') {
        $inTools = $false
    }
    if ($inTools -and $line -match '^\s*-\s*COPPER_AXE\s*$') {
        $changed = $true
        continue
    }
    $line
}

if ($changed) {
    Set-Content -LiteralPath $configPath -Value $filtered -Encoding UTF8
    Write-Output 'TreeFeller config normalized: removed unsupported COPPER_AXE.'
} else {
    Write-Output 'TreeFeller config already normalized.'
}
