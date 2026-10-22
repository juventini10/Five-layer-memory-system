@echo off
rem Buluotuo Windows install fallback launcher (WorkBuddy platform, mechanical install only, no quiz)
rem Keep this file ASCII-only: cmd parses .bat by console codepage, BOM/Chinese here breaks first lines.
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0fallback_install.ps1"
if errorlevel 1 pause
exit /b %ERRORLEVEL%
