# -*- coding: utf-8 -*-
"""
MySQL / MariaDB Auditor and Health Monitor.
Supports deep database metrics, schema sizing, security hardening checks,
processlist monitoring, and two-tier Master PIN protected administration.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import pymysql

logger = logging.getLogger("MySQLAuditor")


class MySQLAuditor:
    """Enterprise MySQL / MariaDB health & security auditor."""

    def __init__(
        self,
        host: str,
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "mysql",
        timeout: int = 5
    ):
        self.host = host.strip()
        self.port = int(port)
        self.user = user.strip()
        self.password = password
        self.database = database.strip() or "mysql"
        self.timeout = timeout

    def _get_connection(self):
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            connect_timeout=self.timeout,
            cursorclass=pymysql.cursors.DictCursor
        )

    def test_connection(self) -> Tuple[bool, str]:
        """Verifies MySQL connection and credentials."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT VERSION() AS ver, DATABASE() AS cur_db")
                row = cur.fetchone()
                ver = row.get("ver", "Unknown") if row else "Unknown"
            conn.close()
            return True, f"เชื่อมต่อสำเร็จ (MySQL Version: {ver})"
        except pymysql.err.OperationalError as e:
            code, msg = e.args[0], e.args[1] if len(e.args) > 1 else str(e)
            if code == 1045:
                return False, "เข้าสู่ระบบไม่สำเร็จ: รหัสผ่านหรือ User MySQL ไม่ถูกต้อง (Access Denied)"
            elif code == 2003:
                return False, f"ไม่สามารถเชื่อมต่อไปยัง Host {self.host}:{self.port} (Connection Refused/Firewall)"
            return False, f"ข้อผิดพลาด: [{code}] {msg}"
        except Exception as e:
            return False, f"เชื่อมต่อล้มเหลว: {str(e)}"

    def run_full_db_audit(self) -> Dict[str, Any]:
        """Gathers complete database status, schemas, security checks, and processlist."""
        result: Dict[str, Any] = {
            "success": False,
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "version": "",
            "uptime_seconds": 0,
            "threads_connected": 0,
            "max_connections": 0,
            "buffer_pool_mb": 0.0,
            "schemas": [],
            "processlist": [],
            "security_checks": [],
            "db_score": 100,
            "error": ""
        }

        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                # 1. Version & Variables
                cur.execute("SELECT VERSION() AS ver")
                row_v = cur.fetchone()
                result["version"] = row_v.get("ver", "") if row_v else ""

                cur.execute("SHOW GLOBAL STATUS LIKE 'Uptime'")
                r_up = cur.fetchone()
                result["uptime_seconds"] = int(r_up["Value"]) if r_up else 0

                cur.execute("SHOW GLOBAL STATUS LIKE 'Threads_connected'")
                r_tc = cur.fetchone()
                result["threads_connected"] = int(r_tc["Value"]) if r_tc else 0

                cur.execute("SHOW GLOBAL VARIABLES LIKE 'max_connections'")
                r_mc = cur.fetchone()
                result["max_connections"] = int(r_mc["Value"]) if r_mc else 151

                cur.execute("SHOW GLOBAL VARIABLES LIKE 'innodb_buffer_pool_size'")
                r_bp = cur.fetchone()
                if r_bp:
                    result["buffer_pool_mb"] = round(int(r_bp["Value"]) / (1024 * 1024), 1)

                # 2. Database Schemas and Sizes
                schema_sql = """
                SELECT 
                    table_schema AS schema_name,
                    COUNT(table_name) AS table_count,
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
                FROM information_schema.TABLES
                GROUP BY table_schema
                ORDER BY size_mb DESC
                """
                cur.execute(schema_sql)
                result["schemas"] = cur.fetchall()

                # 3. Processlist
                cur.execute("SHOW FULL PROCESSLIST")
                all_proc = cur.fetchall()
                result["processlist"] = all_proc

                # 4. Security Hardening Checks
                checks = []
                score = 100

                # Check 4.1: Remote Root User (host = '%')
                try:
                    cur.execute("SELECT user, host FROM mysql.user WHERE user = 'root' AND host = '%'")
                    root_remote = cur.fetchall()
                    if root_remote:
                        checks.append({
                            "check": "Remote Root Access",
                            "status": "CRITICAL",
                            "desc": "พบบัญชี root อนุญาตให้เข้าจากภายนอก (host='%') เสี่ยงต่อการโดน Brute-force สูงมาก"
                        })
                        score -= 30
                    else:
                        checks.append({
                            "check": "Remote Root Access",
                            "status": "PASS",
                            "desc": "บัญชี root ถูกจำกัดให้เข้าได้เฉพาะ localhost (ปลอดภัย)"
                        })
                except Exception:
                    pass

                # Check 4.2: Empty Password Accounts
                try:
                    cur.execute("""
                    SELECT user, host FROM mysql.user 
                    WHERE authentication_string = '' OR authentication_string IS NULL
                    """)
                    empty_pw = cur.fetchall()
                    if empty_pw:
                        names = ", ".join([f"{u['user']}@{u['host']}" for u in empty_pw[:3]])
                        checks.append({
                            "check": "Empty Passwords",
                            "status": "CRITICAL",
                            "desc": f"พบบัญชีผู้ใช้ที่ไม่มีรหัสผ่าน ({names}) ต้องตั้งรหัสผ่านด่วน"
                        })
                        score -= 30
                    else:
                        checks.append({
                            "check": "Empty Passwords",
                            "status": "PASS",
                            "desc": "ผู้ใช้ทุกบัญชีมีรหัสผ่านป้องกัน"
                        })
                except Exception:
                    pass

                # Check 4.3: Binary Logging
                cur.execute("SHOW VARIABLES LIKE 'log_bin'")
                r_bin = cur.fetchone()
                is_binlog = r_bin and r_bin["Value"].upper() in ["ON", "1"]
                if is_binlog:
                    checks.append({
                        "check": "Binary Logging (log_bin)",
                        "status": "PASS",
                        "desc": "เปิด Binary Logging รองรับ Point-in-time recovery และ Replication"
                    })
                else:
                    checks.append({
                        "check": "Binary Logging (log_bin)",
                        "status": "WARNING",
                        "desc": "ปิด Binary Log (หากฐานข้อมูลเสียหายจะไม่สามารถกู้ข้อมูลย้อนหลังระดับวินาทีได้)"
                    })
                    score -= 10

                result["security_checks"] = checks
                result["db_score"] = max(0, score)
                result["success"] = True

            conn.close()
        except Exception as e:
            result["error"] = str(e)

        return result

    def kill_query(self, query_id: int) -> Tuple[bool, str]:
        """Tier 2 Command: Kills a stuck query by ID."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(f"KILL {int(query_id)}")
            conn.close()
            return True, f"ตัดคำสั่งคิวรี ID: {query_id} สำเร็จ"
        except Exception as e:
            return False, f"ไม่สามารถตัดคิวรีได้: {str(e)}"

    def safe_shutdown(self) -> Tuple[bool, str]:
        """Tier 2 Command: Safely shuts down MySQL server."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("SHUTDOWN")
            conn.close()
            return True, "ส่งคำสั่ง SHUTDOWN ไปยัง MySQL Server สำเร็จ"
        except Exception as e:
            # SHUTDOWN command closes connection immediately, which might raise lost connection
            if "Lost connection" in str(e) or "2013" in str(e):
                return True, "MySQL Server กำลังปิดตัวลง (Graceful Shutdown in progress)"
            return False, f"ไม่สามารถส่งคำสั่ง Shutdown ได้: {str(e)}"
