param([string]$PreviewPath, [ValidateSet('inicio','tlauncher','oficial','error')][string]$PreviewState='inicio')
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
. (Join-Path $PSScriptRoot 'installer-common.ps1')
. (Join-Path $PSScriptRoot 'tlauncher-settings.ps1')
[Windows.Forms.Application]::EnableVisualStyles()
$script:worker = $null
$script:choice = 'TLauncher'
$script:installRoot = Join-Path $env:LOCALAPPDATA 'Virgos-MC'
$script:officialRoot = Join-Path $env:APPDATA '.minecraft'
$script:tlConfig = Find-TLauncherSettingsPath
$script:memoryMb = 5120
try {
    $physicalKb = [long](Get-CimInstance Win32_OperatingSystem -ErrorAction Stop).TotalVisibleMemorySize
    if ($physicalKb -ge (15 * 1024 * 1024)) { $script:memoryMb = 6144 }
} catch {}
$script:javaPath = ''
$script:prefsPath = Join-Path $env:LOCALAPPDATA 'Virgos-MC-Instalador\preferencias.json'
if (-not $PreviewPath -and [IO.File]::Exists($script:prefsPath)) {
    try {
        $prefs = Get-Content -LiteralPath $script:prefsPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $script:installRoot = $prefs.installRoot; $script:officialRoot = $prefs.officialRoot
        $script:choice = $prefs.launcher; $script:memoryMb = [int]$prefs.memoryMb
        if($prefs.tlauncherConfig) { $script:tlConfig=$prefs.tlauncherConfig }
    } catch {}
}
$bg = [Drawing.ColorTranslator]::FromHtml('#151b27')
$panel = [Drawing.ColorTranslator]::FromHtml('#202a3b')
$accent = [Drawing.ColorTranslator]::FromHtml('#b3efb0')
$white = [Drawing.ColorTranslator]::FromHtml('#edf2f9')
$muted = [Drawing.ColorTranslator]::FromHtml('#bac8db')
$form = New-Object Windows.Forms.Form
$form.Text = 'Virgos-MC | Preparar mi juego'
$form.ClientSize = New-Object Drawing.Size(810,700)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'; $form.MaximizeBox = $false
$form.BackColor = $bg; $form.ForeColor = $white
$form.Font = New-Object Drawing.Font('Segoe UI',10)
$form.AutoScaleMode = 'Dpi'; $form.AutoScroll = $true
function Label($Text,$X,$Y,$W,$H,$Size=10) {
    $c = New-Object Windows.Forms.Label
    $c.Text=$Text; $c.Location=New-Object Drawing.Point($X,$Y); $c.Size=New-Object Drawing.Size($W,$H)
    $c.Font=New-Object Drawing.Font('Segoe UI',$Size); $form.Controls.Add($c); return $c
}
function Button($Text,$X,$Y,$W) {
    $c=New-Object Windows.Forms.Button
    $c.Text=$Text; $c.Location=New-Object Drawing.Point($X,$Y); $c.Size=New-Object Drawing.Size($W,36)
    $c.FlatStyle='Flat'; $c.BackColor=$panel; $c.ForeColor=$white; $c.Cursor='Hand'
    $form.Controls.Add($c); return $c
}
$title=Label 'VIRGOS-MC' 28 19 650 44 27
$title.ForeColor=$accent
$subtitle=Label 'Tu aventura empieza aca. Elegi tu launcher y prepararemos el juego.' 30 68 750 28
$subtitle.ForeColor=$muted
$tl=New-Object Windows.Forms.RadioButton
$tl.Text='TLauncher'; $tl.Location=New-Object Drawing.Point(40,115); $tl.Size=New-Object Drawing.Size(310,32)
$official=New-Object Windows.Forms.RadioButton
$official.Text='Minecraft Launcher oficial'; $official.Location=New-Object Drawing.Point(384,115); $official.Size=New-Object Drawing.Size(385,32)
$form.Controls.AddRange(@($tl,$official))
$description=Label '' 30 162 750 50
$description.ForeColor=$muted
$install=Button 'Instalar Virgos-MC' 30 221 250
$install.BackColor=$accent; $install.ForeColor=$bg
$options=Button 'Opciones de carpeta y memoria' 440 221 340
$status=Label 'Cierra Minecraft y tu launcher. Despues toca Instalar.' 30 273 750 45
$progress=New-Object Windows.Forms.ProgressBar
$progress.Location=New-Object Drawing.Point(30,324); $progress.Size=New-Object Drawing.Size(750,9)
$form.Controls.Add($progress)
$steps=New-Object Windows.Forms.TextBox
$steps.Location=New-Object Drawing.Point(30,350); $steps.Size=New-Object Drawing.Size(750,224)
$steps.ReadOnly=$true; $steps.BackColor=$panel; $steps.ForeColor=$white; $steps.BorderStyle='None'
$steps.Font=New-Object Drawing.Font('Segoe UI',10); $steps.Multiline=$true; $steps.ScrollBars='Vertical'
$form.Controls.Add($steps)
$copyFolder=Button 'Copiar carpeta' 30 589 170
$restoreTL=Button 'Restaurar TL' 210 589 140
$copyServer=Button 'Copiar servidor' 360 589 175
$logsButton=Button 'Abrir registros' 545 589 235
$openLauncher=Button 'Abrir mi launcher' 30 640 220
$help=Label 'Windows x64  /  Empeza sin shaders  /  COMO-JUGAR.txt: ayuda del juego' 274 647 505 35 9
$help.ForeColor=$muted
function Refresh-Choice {
    $script:choice = if ($official.Checked) {'Oficial'} else {'TLauncher'}
    $script:javaPath = Join-Path $script:installRoot 'runtime\jdk-17.0.20.1+1-jre\bin\javaw.exe'
    if ($script:choice -eq 'Oficial') {
        $description.Text='Creamos un perfil Virgos-MC con Java 17, Forge y memoria configurados. Tus otros perfiles se conservan.'
    } else {
        $description.Text='Configuramos carpeta, Forge y memoria de TLauncher. Guardamos sus ajustes anteriores para que puedas restaurarlos.'
    }
    $steps.Text=Get-LauncherInstructions $script:choice (Join-Path $script:installRoot 'juego') $script:javaPath $script:memoryMb
    $restoreTL.Enabled=($script:choice -eq 'TLauncher' -and -not $script:worker); $copyFolder.Enabled=($script:choice -eq 'TLauncher')
}
$official.Add_CheckedChanged({ Refresh-Choice })
$tl.Add_CheckedChanged({ Refresh-Choice })
if ($script:choice -eq 'Oficial') { $official.Checked=$true } else { $tl.Checked=$true }
Refresh-Choice
$copyFolder.Add_Click({ [Windows.Forms.Clipboard]::SetText((Join-Path $script:installRoot 'juego')); $status.Text='Carpeta copiada. Pegala en Directorio / Directory de TLauncher.' })
$restoreTL.Add_Click({
    try {
        Restore-VirgosTLauncher (Join-Path $script:installRoot 'respaldos-launcher')
        $status.Text='Ajustes anteriores restaurados. Para volver a Virgos-MC, toca Revisar / reparar.'
    } catch { $status.Text=$_.Exception.Message }
})
$copyServer.Add_Click({ [Windows.Forms.Clipboard]::SetText('virgos-mc.playit.plus'); $status.Text='Direccion copiada: virgos-mc.playit.plus' })
$logsButton.Add_Click({
    $p=Join-Path $script:installRoot 'registros'
    if (Test-Path -LiteralPath $p) { Start-Process explorer.exe -ArgumentList ('"'+$p+'"') }
    else { $status.Text='Todavia no hay registros. Aparecen al comenzar la instalacion.' }
})
$openLauncher.Add_Click({
    try {
        $appPattern=if($script:choice -eq 'Oficial'){'^Minecraft Launcher$'}else{'^TLauncher(\s|$)'}
        $app=Get-StartApps -ErrorAction SilentlyContinue | Where-Object Name -Match $appPattern | Select-Object -First 1
        if ($app) { Start-Process explorer.exe -ArgumentList ('shell:AppsFolder\'+$app.AppID); return }
        $dialog=New-Object Windows.Forms.OpenFileDialog
        $dialog.Title='Elegi el archivo de tu launcher ya instalado'; $dialog.Filter='Launcher (*.exe)|*.exe'
        if ($dialog.ShowDialog($form) -eq 'OK') { Start-Process -FilePath $dialog.FileName }
        $dialog.Dispose()
    } catch { $status.Text='Abri tu launcher desde su acceso directo habitual.' }
})
$options.Add_Click({
    $dlg=New-Object Windows.Forms.Form
    $dlg.Text='Carpeta y memoria'; $dlg.ClientSize=New-Object Drawing.Size(670,365)
    $dlg.StartPosition='CenterParent'; $dlg.Font=$form.Font; $dlg.FormBorderStyle='FixedDialog'; $dlg.MaximizeBox=$false
    $labels=@('Instalar Virgos-MC en (crea la subcarpeta juego):','Carpeta del launcher oficial (normalmente no se cambia):','Archivo de ajustes de TLauncher (solo cambiar si es portable):','Memoria para Minecraft:')
    $boxes=@()
    for($i=0;$i -lt 4;$i++) {
        $l=New-Object Windows.Forms.Label; $l.Text=$labels[$i]; $l.SetBounds(18,15+$i*70,630,24); $dlg.Controls.Add($l)
        if($i -lt 3) {
            $t=New-Object Windows.Forms.TextBox; $t.SetBounds(18,40+$i*70,630,28); $dlg.Controls.Add($t); $boxes+=,$t
        }
    }
    $boxes[0].Text=$script:installRoot; $boxes[1].Text=$script:officialRoot; $boxes[2].Text=$script:tlConfig
    $ram=New-Object Windows.Forms.ComboBox; $ram.DropDownStyle='DropDownList'; $ram.SetBounds(18,250,300,30)
    [void]$ram.Items.AddRange(@('5 GB - PC con 12 GB','6 GB - recomendado con 16 GB o mas'))
    $ram.SelectedIndex=if($script:memoryMb -eq 6144){1}else{0}; $dlg.Controls.Add($ram)
    $save=New-Object Windows.Forms.Button; $save.Text='Guardar'; $save.SetBounds(500,312,145,34); $dlg.Controls.Add($save)
    $save.Add_Click({
        try {
            foreach($b in $boxes) { if(-not [IO.Path]::IsPathRooted($b.Text) -or $b.Text -match '[!"\r\n]') { throw 'Usa rutas completas sin signos de admiracion ni comillas.' } }
            $script:installRoot=[IO.Path]::GetFullPath($boxes[0].Text).TrimEnd('\')
            $script:officialRoot=[IO.Path]::GetFullPath($boxes[1].Text).TrimEnd('\')
            $script:tlConfig=[IO.Path]::GetFullPath($boxes[2].Text)
            if($script:installRoot -eq [IO.Path]::GetPathRoot($script:installRoot).TrimEnd('\')) { throw 'Elegi una subcarpeta, por ejemplo D:\Juegos\Virgos-MC.' }
            $script:memoryMb=if($ram.SelectedIndex -eq 1){6144}else{5120}
            $dlg.DialogResult='OK'; $dlg.Close()
        } catch { [void][Windows.Forms.MessageBox]::Show($dlg,$_.Exception.Message,'Revisa la carpeta') }
    })
    [void]$dlg.ShowDialog($form); $dlg.Dispose(); Refresh-Choice
})
$timer=New-Object Windows.Forms.Timer; $timer.Interval=400
$timer.Add_Tick({
    if (-not $script:worker) { return }
    try {
        if([IO.File]::Exists($script:statusFile)) {
            $s=Get-Content -LiteralPath $script:statusFile -Raw -Encoding UTF8 | ConvertFrom-Json
            $progress.Value=[Math]::Max(0,[Math]::Min(100,[int]$s.percent)); $status.Text=$s.message
        }
        if($script:worker.HasExited) {
            $timer.Stop(); $install.Enabled=$true; $options.Enabled=$true; $tl.Enabled=$true; $official.Enabled=$true; $openLauncher.Enabled=$true
            if($s -and $s.state -eq 'complete' -and $script:worker.ExitCode -eq 0) {
                $install.Text='Revisar / reparar'; Refresh-Choice
                $status.ForeColor=$accent
            } else {
                $install.Text='Reintentar'; $status.ForeColor=[Drawing.Color]::LightSalmon
                if(-not $s -or $s.state -eq 'running') { $status.Text='La instalacion se interrumpio. Toca Reintentar; si vuelve a fallar, envia el registro.' }
            }
            $script:worker.Dispose(); $script:worker=$null
            Refresh-Choice
        }
    } catch { $status.Text='Esperando al instalador...' }
})
$install.Add_Click({
    try {
        $script:statusFile=Join-Path $script:installRoot 'registros\estado.json'
        $requestPath=Join-Path $script:installRoot 'registros\solicitud.json'
        $request=@{launcher=$script:choice;installRoot=$script:installRoot;officialRoot=$script:officialRoot;tlauncherConfig=$script:tlConfig;memoryMb=$script:memoryMb;statusPath=$script:statusFile}
        Write-JsonAtomic $requestPath $request; Write-JsonAtomic $script:prefsPath $request
        Write-JsonAtomic $script:statusFile @{state='running';percent=0;message='Preparando la instalacion...'}
        $install.Enabled=$false; $options.Enabled=$false; $tl.Enabled=$false; $official.Enabled=$false; $openLauncher.Enabled=$false
        $restoreTL.Enabled=$false
        $status.ForeColor=$white; $status.Text='Preparando la instalacion...'
        $script:worker=Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+(Join-Path $PSScriptRoot 'install-launcher.ps1')+'"'),'-RequestPath',('"'+$requestPath+'"')) -WindowStyle Hidden -RedirectStandardOutput (Join-Path $script:installRoot 'registros\asistente.log') -RedirectStandardError (Join-Path $script:installRoot 'registros\error.log') -PassThru
        $null=$script:worker.Handle
        $timer.Start()
    } catch {
        $status.Text=$_.Exception.Message; $install.Enabled=$true; $options.Enabled=$true; $tl.Enabled=$true; $official.Enabled=$true; $openLauncher.Enabled=$true
        Refresh-Choice
    }
})
$form.Add_FormClosing({ param($sender,$eventArgs)
    if($script:worker -and -not $script:worker.HasExited) { $eventArgs.Cancel=$true; $status.Text='La instalacion sigue en curso. Espera a que termine antes de cerrar.' }
})
if($PreviewPath) {
    if($PreviewState -eq 'oficial') { $official.Checked=$true }
    if($PreviewState -in @('oficial','tlauncher')) { $status.Text='Instalacion terminada. Segui los pasos de abajo para entrar.'; $progress.Value=100; $install.Text='Revisar / reparar' }
    if($PreviewState -eq 'error') { $status.Text='No se pudo descargar un archivo. Revisa Internet y toca Reintentar.'; $status.ForeColor=[Drawing.Color]::LightSalmon; $install.Text='Reintentar' }
    $form.CreateControl(); $form.Show(); [Windows.Forms.Application]::DoEvents()
    Start-Sleep -Milliseconds 800; [Windows.Forms.Application]::DoEvents()
    $bitmap=New-Object Drawing.Bitmap($form.Width,$form.Height)
    $form.DrawToBitmap($bitmap,(New-Object Drawing.Rectangle(0,0,$form.Width,$form.Height)))
    $bitmap.Save($PreviewPath,[Drawing.Imaging.ImageFormat]::Png); $bitmap.Dispose(); $form.Close()
} else { [void]$form.ShowDialog() }
$timer.Dispose(); $form.Dispose()
