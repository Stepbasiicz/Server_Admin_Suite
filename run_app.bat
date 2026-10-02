@echo off
setlocal enabledelayedexpansion
title Soft4U Server Admin Suite
chcp 65001 >nul
color 0A

cd /d "%~dp0"

echo ========================================================================
echo   Soft4U Server Admin & Security Audit Suite 2026
echo   กำลังเริ่มต้นโปรแกรม...
echo ========================================================================

set "PY_CMD="
python --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PY_CMD=python"
    goto :RUN_APP
)

py --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PY_CMD=py"
    goto :RUN_APP
)

if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
    goto :RUN_APP
)

for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD=%%D\python.exe"
        goto :RUN_APP
    )
)

echo [ERROR] ไม่พบ Python ในระบบ
pause
exit /b 1

:RUN_APP
"!PY_CMD!" main.py
if !errorlevel! neq 0 (
    echo.
    echo โปรแกรมปิดตัวลงด้วยรหัส: !errorlevel!
    pause
)
