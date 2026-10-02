@echo off
setlocal enabledelayedexpansion
title Soft4U Server Admin Suite - Executable Builder
chcp 65001 >nul
color 0B

cd /d "%~dp0"

echo ========================================================================
echo   Soft4U Server Admin & Security Audit Suite 2026
echo   Target: Server_Admin_Suite.exe (Single-File Executable)
echo ========================================================================
echo.

:: Detect Python Command
set "PY_CMD="
python --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PY_CMD=python"
    goto :RUN_BUILD
)

py --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PY_CMD=py"
    goto :RUN_BUILD
)

if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
    goto :RUN_BUILD
)

for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD=%%D\python.exe"
        goto :RUN_BUILD
    )
)

echo [ERROR] ไม่พบ Python ในระบบ กรุณาตรวจสอบการติดตั้ง Python
pause
exit /b 1

:RUN_BUILD
echo [INFO] ใช้ Python: !PY_CMD!
echo.
echo [STAGE 1/2] ตรวจสอบ Dependencies...
"!PY_CMD!" -m pip install -r requirements.txt >nul 2>&1

echo.
echo [STAGE 2/2] เริ่มต้นคอมไพล์ Single EXE ผ่าน build_exe.py...
"!PY_CMD!" build_exe.py

if !errorlevel! equ 0 (
    echo.
    echo ========================================================================
    echo   [SUCCESS] คอมไพล์สำเร็จสมบูรณ์!
    echo   ไฟล์ EXE พร้อมใช้งานอยู่ที่: dist\Server_Admin_Suite.exe
    echo ========================================================================
) else (
    echo.
    color 0C
    echo ========================================================================
    echo   [BUILD FAILED] เกิดข้อผิดพลาดในการคอมไพล์ รหัสข้อผิดพลาด: !errorlevel!
    echo ========================================================================
)
echo.
pause
