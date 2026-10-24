@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar-cliente.ps1" %*
if errorlevel 1 echo No se completo la instalacion. Revisa el error de arriba.
pause
