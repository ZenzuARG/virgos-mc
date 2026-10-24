@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0asistente\asistente.ps1" (
  echo Primero extrae TODO el ZIP: clic derecho, Extraer todo.
  pause
  exit /b 1
)
start "Virgos-MC" "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -STA -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0asistente\asistente.ps1"
