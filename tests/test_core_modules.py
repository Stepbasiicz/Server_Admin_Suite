# -*- coding: utf-8 -*-
"""
Unit tests for Soft4U Server Admin Suite Core Modules.
"""

import os
import sys
import unittest
import shutil

# Include project root
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(TESTS_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.security import SecurityManager, get_machine_hwid
from app.core.config_manager import ConfigManager
from app.core.license_manager import LicenseManager
from app.modules.network_diagnostics import NetworkDiagnostics
from app.modules.pdf_report_generator import PDFReportGenerator


class TestServerAdminCore(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.join(TESTS_DIR, "tmp_test_env")
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_security_manager_aes_gcm(self):
        plain = "SuperSecret_Admin_Password_2026!@#"
        enc = SecurityManager.encrypt_text(plain)
        self.assertTrue(enc.startswith("ENC:GCM:"))
        dec = SecurityManager.decrypt_text(enc)
        self.assertEqual(dec, plain)

    def test_security_manager_binary_vault(self):
        payload = {"server": "192.168.1.1", "secret": "xyz123", "ports": [22, 3306]}
        vault_bytes = SecurityManager.encrypt_vault_payload(payload)
        self.assertIn(b"\x89S4U\x02\x00\x00\x00", vault_bytes)

        unpacked = SecurityManager.decrypt_vault_payload(vault_bytes)
        self.assertIsNotNone(unpacked)
        self.assertEqual(unpacked["server"], "192.168.1.1")
        self.assertEqual(unpacked["ports"], [22, 3306])

    def test_config_manager_encrypted_persistence(self):
        cfg_mgr = ConfigManager(base_dir=self.test_dir)
        test_server = {
            "id": "srv_unit_test",
            "name": "Unit Test Server",
            "host": "10.0.0.99",
            "ssh_port": 2222,
            "ssh_user": "admin",
            "ssh_password": "PlainPasswordToEncrypt",
            "mysql_port": 3306,
            "mysql_user": "dbuser",
            "mysql_password": "MyDbPassword"
        }
        cfg_mgr.add_or_update_server(test_server)

        # Reload with new instance from the same directory
        cfg_mgr2 = ConfigManager(base_dir=self.test_dir)
        retrieved = cfg_mgr2.get_server_by_id("srv_unit_test")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["host"], "10.0.0.99")
        self.assertEqual(retrieved["ssh_password"], "PlainPasswordToEncrypt")

        # Verify on-disk file is binary vault, not plaintext
        dat_path = os.path.join(self.test_dir, "config.dat")
        self.assertTrue(os.path.exists(dat_path))
        with open(dat_path, "rb") as f:
            raw = f.read()
        self.assertNotIn(b"PlainPasswordToEncrypt", raw)

    def test_network_ping_localhost(self):
        res = NetworkDiagnostics.ping("127.0.0.1", count=1, timeout_ms=1000)
        self.assertEqual(res["host"], "127.0.0.1")
        self.assertTrue(res["success"])
        self.assertEqual(res["packet_loss_pct"], 0)

    def test_pdf_report_generation(self):
        reports_dir = os.path.join(self.test_dir, "reports")
        gen = PDFReportGenerator(output_dir=reports_dir)

        dummy_linux = {
            "success": True,
            "os_info": {"distro": "Ubuntu 22.04.4 LTS", "kernel": "5.15.0-generic", "arch": "x86_64", "hostname": "srv-prod-01"},
            "uptime_load": {"raw_uptime": "up 45 days", "load_1m": 0.42, "load_5m": 0.35, "load_15m": 0.28},
            "resources": {"cpu_cores": 8, "ram_total_mb": 16000, "ram_used_mb": 4200, "ram_free_mb": 11800, "ram_pct": 26.2, "swap_total_mb": 8000, "swap_used_mb": 0, "swap_pct": 0},
            "disks": [{"filesystem": "/dev/sda1", "size": "100G", "used": "25G", "avail": "75G", "use_pct": 25, "mount": "/"}],
            "firewall": {"type": "UFW", "is_active": True, "status_detail": "Active (Status: active)"},
            "patches": {"total_upgrades": 0, "security_upgrades": 0, "status_text": "ระบบเป็นเวอร์ชันล่าสุด 100%"},
            "security_score": 95,
            "security_grade": "A+",
            "security_findings": [
                {"category": "Firewall", "status": "PASS", "desc": "Firewall เปิดใช้งาน (UFW)"},
                {"category": "OS Patches", "status": "PASS", "desc": "ระบบเป็นเวอร์ชันล่าสุด"}
            ]
        }

        dummy_mysql = {
            "success": True,
            "version": "10.5.18-MariaDB",
            "uptime_seconds": 360000,
            "threads_connected": 8,
            "max_connections": 300,
            "buffer_pool_mb": 4096.0,
            "schemas": [{"schema_name": "hosxp_pcu", "table_count": 340, "size_mb": 1420.5}],
            "security_checks": [
                {"check": "Remote Root", "status": "PASS", "desc": "บัญชี root ถูกจำกัดเฉพาะ localhost"}
            ]
        }

        pdf_path = gen.generate_audit_report(
            server_name="Hospital Production Database",
            host="192.168.1.10",
            linux_audit=dummy_linux,
            mysql_audit=dummy_mysql
        )

        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 1000)


if __name__ == "__main__":
    unittest.main()
