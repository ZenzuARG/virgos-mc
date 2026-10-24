@echo off
set "PSModulePath=%SystemRoot%\System32\WindowsPowerShell\v1.0\Modules"
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\abrir-panel.ps1"
if errorlevel 1 pause
