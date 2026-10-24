Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
folder = files.GetParentFolderName(WScript.ScriptFullName)
shell.Run "powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File """ & folder & "\abrir-panel.ps1""", 0, False
