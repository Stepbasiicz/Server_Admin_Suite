# -*- coding: utf-8 -*-
"""
Configuration Manager with Dual-Layer Encrypted Vault Storage.
Manages server connection profiles, credentials, and app preferences.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from app.core.security import SecurityManager

logger = logging.getLogger("ConfigManager")

DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "261002.2315",
    "theme": "Dark",
    "dynamic_font": "Leelawadee UI",
    "audit_defaults": {
        "ping_count": 4,
        "ping_timeout_sec": 2,
        "port_scan_timeout_sec": 1.0,
        "standard_ports": [21, 22, 25, 53, 80, 110, 143, 443, 3306, 5432, 6379, 8080, 8443],
        "ssh_timeout_sec": 8,
        "mysql_timeout_sec": 5,
        "pdf_output_dir": "reports",
        "master_pin": "ENC:GCM:admin"
    },
    "servers": [
        {
            "id": "srv_default_sample",
            "name": "Local Test Server (127.0.0.1)",
            "host": "127.0.0.1",
            "ssh_port": 22,
            "ssh_user": "root",
            "ssh_password": "",
            "ssh_key_path": "",
            "mysql_port": 3306,
            "mysql_user": "root",
            "mysql_password": "",
            "mysql_db": "mysql",
            "notes": "ตัวอย่างเซิร์ฟเวอร์เริ่มต้นสำหรับทดสอบ"
        }
    ]
}


class ConfigManager:
    """Enterprise Configuration Manager saving encrypted binary config."""

    _instance = None
    _config: Dict[str, Any] = {}
    _base_dir: str = ""
    _dat_file: str = ""
    _json_file: str = ""

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            if getattr(sys, "frozen", False):
                self._base_dir = os.path.dirname(sys.executable)
            else:
                self._base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        else:
            self._base_dir = base_dir

        self._dat_file = os.path.join(self._base_dir, "config.dat")
        self._json_file = os.path.join(self._base_dir, "config.json")
        self.load()

    @classmethod
    def get_instance(cls, base_dir: Optional[str] = None) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = ConfigManager(base_dir)
        return cls._instance

    def load(self) -> Dict[str, Any]:
        """Load configuration from Binary Vault (.dat) or fallback to Plain JSON."""
        # 1. Try Binary Vault .dat
        if os.path.exists(self._dat_file):
            try:
                with open(self._dat_file, "rb") as f:
                    raw = f.read()
                data = SecurityManager.decrypt_vault_payload(raw)
                if data and isinstance(data, dict):
                    self._config = data
                    self._decrypt_sensitive_fields()
                    return self._config
            except Exception as e:
                logger.error(f"Failed loading config.dat: {e}")

        # 2. Try JSON file
        if os.path.exists(self._json_file):
            try:
                with open(self._json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self._config = data
                    self._decrypt_sensitive_fields()
                    # Auto migrate to .dat
                    self.save()
                    return self._config
            except Exception as e:
                logger.error(f"Failed loading config.json: {e}")

        # 3. Default fallback
        self._config = json.loads(json.dumps(DEFAULT_CONFIG))
        self.save()
        return self._config

    def save(self) -> bool:
        """Encrypt sensitive credentials and save as Dual-Layer Binary Vault (.dat)."""
        try:
            cfg_copy = json.loads(json.dumps(self._config))
            self._encrypt_sensitive_fields(cfg_copy)

            # Write binary vault
            binary_payload = SecurityManager.encrypt_vault_payload(cfg_copy)
            with open(self._dat_file, "wb") as f:
                f.write(binary_payload)

            return True
        except Exception as e:
            logger.error(f"Failed saving encrypted config: {e}")
            return False

    def _decrypt_sensitive_fields(self):
        """Decrypt in-memory fields so the app can use plaintext credentials."""
        servers = self._config.get("servers", [])
        for s in servers:
            if "ssh_password" in s:
                s["ssh_password"] = SecurityManager.decrypt_text(s["ssh_password"])
            if "mysql_password" in s:
                s["mysql_password"] = SecurityManager.decrypt_text(s["mysql_password"])

        audit = self._config.get("audit_defaults", {})
        if "master_pin" in audit:
            audit["master_pin"] = SecurityManager.decrypt_text(audit["master_pin"])

    def _encrypt_sensitive_fields(self, cfg_copy: dict):
        """Convert plaintext passwords to ENC:GCM:... before serialization."""
        servers = cfg_copy.get("servers", [])
        for s in servers:
            if "ssh_password" in s and s["ssh_password"]:
                s["ssh_password"] = SecurityManager.encrypt_text(s["ssh_password"])
            if "mysql_password" in s and s["mysql_password"]:
                s["mysql_password"] = SecurityManager.encrypt_text(s["mysql_password"])

        audit = cfg_copy.get("audit_defaults", {})
        if "master_pin" in audit and audit["master_pin"]:
            audit["master_pin"] = SecurityManager.encrypt_text(audit["master_pin"])

    # Helper getters and setters
    def get_servers(self) -> List[Dict[str, Any]]:
        return self._config.get("servers", [])

    def get_server_by_id(self, srv_id: str) -> Optional[Dict[str, Any]]:
        for s in self.get_servers():
            if s.get("id") == srv_id:
                return s
        return None

    def add_or_update_server(self, server_dict: Dict[str, Any]) -> bool:
        servers = self._config.setdefault("servers", [])
        srv_id = server_dict.get("id")
        found = False
        for i, s in enumerate(servers):
            if s.get("id") == srv_id:
                servers[i] = server_dict
                found = True
                break
        if not found:
            servers.append(server_dict)
        return self.save()

    def delete_server(self, srv_id: str) -> bool:
        servers = self._config.get("servers", [])
        self._config["servers"] = [s for s in servers if s.get("id") != srv_id]
        return self.save()

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set_setting(self, key: str, value: Any) -> bool:
        self._config[key] = value
        return self.save()

    def get_audit_defaults(self) -> Dict[str, Any]:
        return self._config.get("audit_defaults", DEFAULT_CONFIG["audit_defaults"])
