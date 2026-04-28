@echo off
setlocal

set "PROJECT_DIR=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_DIR%install_weekly_task.ps1"

endlocal
