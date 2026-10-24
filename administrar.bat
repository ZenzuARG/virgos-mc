@echo off
setlocal
cd /d "%~dp0"
call "%~dp0panel.bat" %*
exit /b %ERRORLEVEL%
