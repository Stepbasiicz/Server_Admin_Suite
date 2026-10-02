# -*- coding: utf-8 -*-
"""
Soft4UApp Enterprise Auto-Updater Engine.
Provides PowerShell External Process Helper for Zero-File-Lock Auto-Updating,
supporting both Remote GitHub Releases and Local File Simulation.
"""

import os
import sys
import json
import time
import logging
import subprocess
import urllib.request
import ssl
from typing import Dict, Any, Tuple, Optional
from version import APP_VERSION, DEFAULT_MANIFEST_URL

logger = logging.getLogger("AutoUpdater")


class AutoUpdater:
    """Manages update discovery, binary download, and Windows PowerShell swap."""

    def __init__(self, manifest_url: str = DEFAULT_MANIFEST_URL):
        self.manifest_url = manifest_url
        self.current_version = APP_VERSION

    @staticmethod
    def is_newer_version(latest_str: str, current_str: str) -> bool:
        """Compare timestamp or semantic versioning strings."""
        try:
            l_clean = latest_str.replace("v", "").replace(".", "").strip()
            c_clean = current_str.replace("v", "").replace(".", "").strip()
            return int(l_clean) > int(c_clean)
        except Exception:
            return latest_str != current_str

    def check_for_updates(self, custom_url: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Queries manifest URL (or local json) for newer release.
        Returns: (has_update, manifest_dict, status_message)
        """
        url = custom_url or self.manifest_url
        if not url:
            return False, None, "ไม่ได้ระบุ URL สำหรับตรวจสอบการอัปเดต"

        # 1. Local File Check (for offline testing)
        if os.path.exists(url) or url.startswith("file://"):
            try:
                local_path = url.replace("file://", "")
                with open(local_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                latest_ver = data.get("latest_version") or data.get("version", "")
                has_up = self.is_newer_version(latest_ver, self.current_version)
                msg = f"พบเวอร์ชันใหม่: v{latest_ver}" if has_up else f"คุณกำลังใช้งานเวอร์ชันล่าสุด (v{self.current_version})"
                return has_up, data, msg
            except Exception as e:
                return False, None, f"ไม่สามารถอ่านไฟล์ Manifest: {e}"

        # 2. Remote HTTP(S) Check
        if not url.startswith("http"):
            return False, None, "URL ไม่ถูกต้อง (ต้องขึ้นต้นด้วย http:// หรือ https://)"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Soft4UApp-Updater",
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }

        try:
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            sep = "&" if "?" in url else "?"
            fresh_url = f"{url}{sep}_nocache={int(time.time())}"

            req = urllib.request.Request(fresh_url, headers=headers)
            with urllib.request.urlopen(req, timeout=6, context=ssl_ctx) as resp:
                if resp.getcode() == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    latest_ver = data.get("latest_version") or data.get("version", "")
                    has_up = self.is_newer_version(latest_ver, self.current_version)
                    msg = f"พบเวอร์ชันใหม่: v{latest_ver}" if has_up else f"คุณกำลังใช้งานเวอร์ชันล่าสุด (v{self.current_version})"
                    return has_up, data, msg
                else:
                    err_code = resp.getcode()
                    if err_code == 404:
                        # Try local version.json in app directory
                        app_dir = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
                        local_json = os.path.join(app_dir, "version.json")
                        if os.path.exists(local_json):
                            try:
                                with open(local_json, "r", encoding="utf-8") as f:
                                    data = json.load(f)
                                latest_ver = data.get("latest_version") or data.get("version", "")
                                has_up = self.is_newer_version(latest_ver, self.current_version)
                                msg = f"พบเวอร์ชันใหม่ (ตรวจพบ version.json ในโฟลเดอร์): v{latest_ver}" if has_up else f"คุณกำลังใช้งานเวอร์ชันล่าสุด (v{self.current_version})"
                                return has_up, data, msg
                            except Exception:
                                pass
                        return False, None, "ยังไม่พบ Repository หรือไฟล์ version.json บน GitHub (HTTP 404)\nเนื่องจากโปรเจกต์นี้ยังไม่ได้สร้าง Release บน GitHub\n\n💡 คุณสามารถทดสอบการสลับไฟล์อัปเดตได้ผ่านปุ่ม '🧪 ทดสอบสลับไฟล์อัปเดต' ในแท็บตั้งค่าครับ"
                    return False, None, f"HTTP Error {err_code}"
        except Exception as e:
            # Fallback: check local version.json
            app_dir = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
            local_json = os.path.join(app_dir, "version.json")
            if os.path.exists(local_json):
                try:
                    with open(local_json, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    latest_ver = data.get("latest_version") or data.get("version", "")
                    has_up = self.is_newer_version(latest_ver, self.current_version)
                    msg = f"พบเวอร์ชันใหม่ (ตรวจพบ version.json ในเครื่อง): v{latest_ver}" if has_up else f"คุณกำลังใช้งานเวอร์ชันล่าสุด (v{self.current_version})"
                    return has_up, data, msg
                except Exception:
                    pass

            err_str = str(e)
            if "404" in err_str:
                return False, None, "ยังไม่พบ Repository หรือไฟล์ version.json บน GitHub (HTTP 404)\nเนื่องจากโปรเจกต์นี้ยังไม่ได้สร้าง Release บน GitHub\n\n💡 คุณสามารถทดสอบการสลับไฟล์อัปเดตได้ผ่านปุ่ม '🧪 ทดสอบสลับไฟล์อัปเดต' ในแท็บตั้งค่าครับ"
            return False, None, f"ไม่สามารถตรวจสอบอัปเดตได้: {err_str}"

    def download_and_apply_update(self, download_url_or_path: str, latest_ver: str = "") -> Tuple[bool, str]:
        """
        Executes external PowerShell helper to replace the running executable.
        Supports both HTTP URL download and local file copy.
        Main process terminates immediately with os._exit(0) to release file lock.
        """
        if sys.platform != "win32":
            return False, "ระบบ Auto-Update รองรับเฉพาะ Windows"

        current_exe_path = sys.executable if getattr(sys, "frozen", False) else os.path.abspath("Server_Admin_Suite.exe")
        app_dir = os.path.dirname(current_exe_path)
        current_pid = os.getpid()

        ps_script_path = os.path.join(app_dir, "_run_update.ps1")
        temp_exe = os.path.join(app_dir, "_new_version.tmp")

        # Determine download command vs local file copy
        is_remote = download_url_or_path.startswith("http")
        if is_remote:
            fetch_cmd = f"""
Write-Host "[2/3] Downloading new version from server..." -ForegroundColor Cyan
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
$webClient = New-Object System.Net.WebClient
$webClient.Headers.Add("User-Agent", "Mozilla/5.0 Windows NT 10.0")
try {{
    $webClient.DownloadFile("{download_url_or_path}", $tempExe)
    Write-Host "      Download completed successfully!" -ForegroundColor Green
}} catch {{
    Write-Host "      Download failed: $_" -ForegroundColor Red
    Start-Sleep -Seconds 5
    Exit 1
}}
"""
        else:
            local_src = os.path.abspath(download_url_or_path.replace("file://", ""))
            fetch_cmd = f"""
Write-Host "[2/3] Copying new version binary from local source..." -ForegroundColor Cyan
try {{
    Copy-Item -Path "{local_src}" -Destination $tempExe -Force
    Write-Host "      Source file copied successfully!" -ForegroundColor Green
}} catch {{
    Write-Host "      Failed to copy: $_" -ForegroundColor Red
    Start-Sleep -Seconds 5
    Exit 1
}}
"""

        ps_content = f"""# Soft4UApp Auto-Updater Helper
$Host.UI.RawUI.WindowTitle = "Soft4UApp Auto-Updater - Updating to v{latest_ver}"
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Soft4UApp Auto-Updater Engine 2026" -ForegroundColor Yellow
Write-Host "  Target Application: Server_Admin_Suite.exe" -ForegroundColor White
Write-Host "  Updating to version: v{latest_ver}" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Waiting for main process (PID: {current_pid}) to terminate..." -ForegroundColor Gray
Start-Sleep -Seconds 2
Stop-Process -Id {current_pid} -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

$targetExe = "{current_exe_path}"
$tempExe = "{temp_exe}"

{fetch_cmd}

Write-Host "[3/3] Swapping executable and restarting application..." -ForegroundColor Cyan
if (Test-Path $tempExe) {{
    $retryCount = 0
    $moved = $false
    while (-not $moved -and $retryCount -lt 15) {{
        try {{
            Move-Item -Path $tempExe -Destination $targetExe -Force -ErrorAction Stop
            $moved = $true
        }} catch {{
            $retryCount++
            Write-Host "      Waiting for file unlock (Retry $retryCount/15)..." -ForegroundColor Yellow
            Start-Sleep -Milliseconds 600
        }}
    }}

    if ($moved) {{
        # Clean PyInstaller environment variables
        Get-ChildItem env:* | Where-Object {{ $_.Name -match '^(_MEI|_PYI|PYI)' }} | ForEach-Object {{ Remove-Item "env:$($_.Name)" -ErrorAction SilentlyContinue }}

        Write-Host "      Update successful! Starting updated application..." -ForegroundColor Green
        Start-Sleep -Seconds 1
        Start-Process -FilePath $targetExe -WorkingDirectory "{app_dir}"
    }} else {{
        Write-Host "      Failed to replace executable (file locked by another process)." -ForegroundColor Red
        Start-Sleep -Seconds 5
        Exit 1
    }}
}}

Start-Sleep -Seconds 1
Remove-Item -Path $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
Exit 0
"""
        try:
            with open(ps_script_path, "w", encoding="utf-8") as pf:
                pf.write(ps_content)

            # Clean PyInstaller environment variables
            clean_env = os.environ.copy()
            for k in list(clean_env.keys()):
                if k.upper().startswith(("_MEI", "_PYI", "PYI")):
                    clean_env.pop(k, None)

            # Spawn independent PowerShell process
            subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_script_path],
                cwd=app_dir,
                env=clean_env,
                creationflags=0x00000010  # CREATE_NEW_CONSOLE
            )

            # Exit immediately so targetExe is unlocked
            os._exit(0)
            return True, "Triggered update process successfully"
        except Exception as e:
            logger.error(f"Failed to trigger PowerShell update: {e}")
            return False, f"เกิดข้อผิดพลาดในการเริ่มสคริปต์อัปเดต: {str(e)}"
