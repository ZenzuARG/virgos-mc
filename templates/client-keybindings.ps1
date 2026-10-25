# Pure controls migration; file writes use the installer's existing atomic helpers.
function Merge-VirgosKeyBindings([string]$Text, $Policy) {
    if ($Policy.schema -ne 1 -or -not $Policy.bindings) { throw 'Unknown controls policy.' }
    $values=[ordered]@{}
    $lines=New-Object Collections.Generic.List[string]
    foreach($line in ($Text -split '\r?\n')) {
        if($line -match '^key_([^:]+):(.+)$') {
            if($values.Contains($Matches[1])) { throw ('Duplicate control: '+$Matches[1]) }
            $values[$Matches[1]]=$Matches[2]
        }
        $lines.Add($line)
    }
    $own='key.virgos_codex.open'; $legacy='key.heracles.open_quests'; $unbound='key.keyboard.unknown'
    if(( -not $values.Contains($own) -or $values[$own] -eq $unbound) -and $values.Contains($legacy) -and $values[$legacy] -ne $unbound) {
        $values[$own]=$values[$legacy]
    }
    foreach($property in $Policy.bindings.PSObject.Properties) {
        $name=$property.Name; $rule=$property.Value
        if(-not $values.Contains($name) -or @($rule.previous) -contains $values[$name] -or ($rule.repairUnbound -and $values[$name] -eq $unbound)) {
            $values[$name]=[string]$rule.key
        }
    }
    $values[$legacy]=$unbound
    $seen=@{}
    for($i=0;$i -lt $lines.Count;$i++) {
        if($lines[$i] -match '^key_([^:]+):') {
            $name=$Matches[1]
            if($Policy.bindings.PSObject.Properties[$name]) { $lines[$i]='key_'+$name+':'+$values[$name] }
            $seen[$name]=$true
        }
    }
    while($lines.Count -gt 0 -and $lines[$lines.Count-1] -eq '') { $lines.RemoveAt($lines.Count-1) }
    foreach($name in $values.Keys) {
        if(-not $seen.ContainsKey($name)) { $lines.Add('key_'+$name+':'+$values[$name]) }
    }
    $byKey=@{}
    foreach($name in $values.Keys) {
        $rule=$Policy.bindings.PSObject.Properties[$name]
        if($values[$name] -ne $unbound -and (($rule -and $rule.Value.context -eq 'global') -or @($Policy.preserve) -contains $name)) {
            $key=[string]$values[$name]
            if(-not $byKey.ContainsKey($key)) { $byKey[$key]=New-Object Collections.Generic.List[string] }
            $byKey[$key].Add($name)
        }
    }
    $conflicts=@($byKey.Keys | Sort-Object | Where-Object { $byKey[$_].Count -gt 1 } | ForEach-Object {
        [pscustomobject]@{key=$_;actions=@($byKey[$_])}
    })
    $newline=if($Text.Contains("`r`n")){"`r`n"}else{"`n"}
    return [pscustomobject]@{Text=($lines -join $newline)+$newline;Conflicts=$conflicts}
}

function Get-VirgosKeyBindingsPlan([string]$OptionsPath,[string]$PolicyPath,[string]$DefaultOptionsPath) {
    $original=if([IO.File]::Exists($OptionsPath)){[IO.File]::ReadAllText($OptionsPath)}else{''}
    $text=$original
    if(-not [IO.File]::Exists($OptionsPath) -and $DefaultOptionsPath -and [IO.File]::Exists($DefaultOptionsPath)) {
        $text=[IO.File]::ReadAllText($DefaultOptionsPath)
    }
    $policy=Get-Content -LiteralPath $PolicyPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $result=Merge-VirgosKeyBindings $text $policy
    return [pscustomobject]@{OptionsPath=$OptionsPath;OriginalText=$original;Text=$result.Text;Conflicts=@($result.Conflicts)}
}

function Write-VirgosKeyBindingsPlan($Plan) {
    # The installer validates and computes this plan before modifying any installed files.
    if($Plan.Text -cne $Plan.OriginalText) { Write-TextAtomic $Plan.OptionsPath $Plan.Text }
    $report=Join-Path ([IO.Path]::GetDirectoryName($Plan.OptionsPath)) 'virgos-keybinding-conflicts.json'
    Write-JsonAtomic $report @{schema=1;conflicts=@($Plan.Conflicts)}
    if(@($Plan.Conflicts).Count) { Write-Warning 'Se conservaron controles personales con conflictos. Revise Controles y virgos-keybinding-conflicts.json.' }
}

function Set-VirgosKeyBindings([string]$OptionsPath,[string]$PolicyPath) {
    $plan=Get-VirgosKeyBindingsPlan $OptionsPath $PolicyPath
    Write-VirgosKeyBindingsPlan $plan
}
