@echo off
powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0Install.ps1" -Action Install
set "result=%ERRORLEVEL%"
echo.
pause
exit /b %result%
