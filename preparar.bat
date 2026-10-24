@echo off
setlocal
set "PSModulePath=%ProgramFiles%\WindowsPowerShell\Modules;%SystemRoot%\System32\WindowsPowerShell\v1.0\Modules"
title Preparar Minecraft 1.20.1
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\preparar.ps1"
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%

