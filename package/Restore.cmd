@echo off
powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0Install.ps1" -Action Restore
set "result=%ERRORLEVEL%"
echo.
pause
exit /b %result%
