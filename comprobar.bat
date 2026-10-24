@echo off
setlocal
set "PSModulePath=%ProgramFiles%\WindowsPowerShell\Modules;%SystemRoot%\System32\WindowsPowerShell\v1.0\Modules"
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\comprobar.ps1" %*
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%

