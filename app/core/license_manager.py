# -*- coding: utf-8 -*-
"""
Soft4UApp Universal Licensing & Anti-Tamper 7-Day Trial Engine.
Enterprise Architecture Standard (Ultimate 2026+)
"""

import os
import sys
import json
import time
import base64
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from app.core.security import get_machine_hwid, SecurityManager

MASTER_SECRET = b"Soft4UApp_DBTools_License_MasterSecret_Key_2026_AuthVault"
TRIAL_DAYS = 7


class LicenseManager:
    """Enterprise License & Triple-Anchor Trial Verification."""

    APP_ID = "APP_SERVER_ADMIN_TOOL"
    ALL_SUITE_ID = "APP_ALL_SUITE"

    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.hwid = get_machine_hwid()
        self._app_hash = hashlib.sha256(self.APP_ID.encode("utf-8")).hexdigest()[:12]

    # --- License Verification ---
    def verify_license_key(self, key_string: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verifies license key with HMAC-SHA256 signature against this machine HWID.
        Returns: (is_valid, message, info_dict)
        """
        if not key_string or not isinstance(key_string, str):
            return False, "กรุณาระบุ License Key", {}

        key_clean = key_string.strip()
        parts = key_clean.split(".")
        if len(parts) != 2:
            return False, "รูปแบบ License Key ไม่ถูกต้อง (Missing signature)", {}

        payload_b64, signature_hex = parts[0], parts[1]

        try:
            payload_json = base64.b64decode(payload_b64.encode("ascii")).decode("utf-8")
            data = json.loads(payload_json)
        except Exception:
            return False, "ข้อมูลใน License Key เสียหาย", {}

        # 1. Dual HMAC-SHA256 verification
        expected_sig = hmac.new(MASTER_SECRET, payload_b64.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, signature_hex):
            # Check raw json fallback
            expected_sig_raw = hmac.new(MASTER_SECRET, payload_json.encode("utf-8"), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected_sig_raw, signature_hex):
                return False, "ลายเซ็น License Key ไม่ถูกต้อง (Invalid Signature)", {}

        # 2. App ID verification
        target_app = data.get("app_id", "")
        if target_app != self.APP_ID and target_app != self.ALL_SUITE_ID:
            return False, f"License นี้สำหรับโปรแกรม '{target_app}' ไม่สามารถใช้กับโปรแกรมนี้ได้", {}

        # 3. Hardware binding verification
        licensed_hwid = data.get("hwid", "")
        if licensed_hwid != "ANY_DEVICE" and licensed_hwid != self.hwid:
            return False, "License นี้ผูกกับเครื่องคอมพิวเตอร์เครื่องอื่น", {}

        # 4. Expiry verification
        exp_date_str = data.get("expiry_date", "")
        if exp_date_str and exp_date_str != "LIFETIME":
            try:
                exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d")
                if datetime.now() > exp_date:
                    return False, f"License หมดอายุแล้วเมื่อวันที่ {exp_date_str}", data
            except ValueError:
                return False, "รูปแบบวันหมดอายุใน License ไม่ถูกต้อง", {}

        return True, "License ถูกต้องสมบูรณ์ (Activated)", data

    # --- Triple-Anchor 7-Day Trial Engine ---
    def get_trial_status(self) -> Dict[str, Any]:
        """
        Evaluates trial remaining using Triple-Anchor storage:
        1. Local Config (Encrypted)
        2. Windows Registry
        3. Hidden AppData
        With Anti-Clock Rollback protection.
        """
        now = datetime.now()
        now_ts = int(now.timestamp())

        # Anchor 1: Local
        local_start, local_last = self._read_local_anchor()
        # Anchor 2: Registry
        reg_start, reg_last = self._read_registry_anchor()
        # Anchor 3: Hidden AppData
        appdata_start, appdata_last = self._read_appdata_anchor()

        # Combine anchors
        starts = [s for s in [local_start, reg_start, appdata_start] if s > 0]
        lasts = [l for l in [local_last, reg_last, appdata_last] if l > 0]

        first_start = min(starts) if starts else now_ts
        highest_last = max(lasts) if lasts else now_ts

        # Anti-Clock Rollback detection
        is_rollback = False
        if now_ts < (highest_last - 3600):  # Machine time shifted backwards more than 1 hr
            is_rollback = True

        # Update last seen to now
        current_last = max(highest_last, now_ts)
        self._write_all_anchors(first_start, current_last)

        start_dt = datetime.fromtimestamp(first_start)
        expiry_dt = start_dt + timedelta(days=TRIAL_DAYS)
        days_left = max(0, (expiry_dt - now).days)
        seconds_left = max(0, int((expiry_dt - now).total_seconds()))

        is_expired = (now >= expiry_dt) or is_rollback

        return {
            "is_expired": is_expired,
            "days_left": days_left,
            "seconds_left": seconds_left,
            "start_date": start_dt.strftime("%Y-%m-%d"),
            "expiry_date": expiry_dt.strftime("%Y-%m-%d"),
            "is_clock_tampered": is_rollback,
            "hwid": self.hwid
        }

    def _read_local_anchor(self) -> Tuple[int, int]:
        if not self.config_manager:
            return 0, 0
        t_data = self.config_manager.get_setting("_trial_anchor", {})
        return t_data.get("s", 0), t_data.get("l", 0)

    def _read_registry_anchor(self) -> Tuple[int, int]:
        if sys.platform != "win32":
            return 0, 0
        try:
            import winreg
            key_path = rf"Software\Soft4UApp\{self._app_hash}"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                s, _ = winreg.QueryValueEx(key, "ts_s")
                l, _ = winreg.QueryValueEx(key, "ts_l")
                return int(s), int(l)
        except Exception:
            return 0, 0

    def _read_appdata_anchor(self) -> Tuple[int, int]:
        try:
            appdata = os.environ.get("LOCALAPPDATA", "")
            if not appdata:
                return 0, 0
            path = os.path.join(appdata, f".s4u_{self._app_hash}.dat")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return int(data.get("s", 0)), int(data.get("l", 0))
        except Exception:
            pass
        return 0, 0

    def _write_all_anchors(self, start_ts: int, last_ts: int):
        # 1. Local
        if self.config_manager:
            self.config_manager.set_setting("_trial_anchor", {"s": start_ts, "l": last_ts})

        # 2. Registry
        if sys.platform == "win32":
            try:
                import winreg
                key_path = rf"Software\Soft4UApp\{self._app_hash}"
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                    winreg.SetValueEx(key, "ts_s", 0, winreg.REG_SZ, str(start_ts))
                    winreg.SetValueEx(key, "ts_l", 0, winreg.REG_SZ, str(last_ts))
            except Exception:
                pass

        # 3. AppData
        try:
            appdata = os.environ.get("LOCALAPPDATA", "")
            if appdata:
                path = os.path.join(appdata, f".s4u_{self._app_hash}.dat")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"s": start_ts, "l": last_ts}, f)
        except Exception:
            pass
