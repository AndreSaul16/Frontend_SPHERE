@echo off
REM ============================================
REM SPHERE v3-TheLastDance — Deploy (double-click)
REM ============================================
echo.
echo   SPHERE v3 — Deploy Express
echo   ==========================
echo.
echo   Running PowerShell deploy script...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0deploy.ps1"

echo.
echo   Script finished. Press any key to exit...
pause >nul
