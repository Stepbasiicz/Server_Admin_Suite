# -*- coding: utf-8 -*-
"""
Linux Server SSH Auditor Module.
Connects via SSH to perform deep health checks, firewall audits, storage inspections,
and OS patch/security update verifications.
"""

import re
import socket
import logging
from typing import Dict, Any, List, Optional, Tuple
import paramiko

logger = logging.getLogger("LinuxSSHAuditor")


class LinuxSSHAuditor:
    """Performs comprehensive security and health audits on Linux servers via SSH."""

    def __init__(
        self,
        host: str,
        port: int = 22,
        user: str = "root",
        password: Optional[str] = None,
        key_filename: Optional[str] = None,
        timeout: int = 8
    ):
        self.host = host.strip()
        self.port = int(port)
        self.user = user.strip()
        self.password = password
        self.key_filename = key_filename if (key_filename and key_filename.strip()) else None
        self.timeout = timeout
        self.client: Optional[paramiko.SSHClient] = None

    def connect(self) -> Tuple[bool, str]:
        """Establishes SSH connection."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs = {
                "hostname": self.host,
                "port": self.port,
                "username": self.user,
                "timeout": self.timeout,
                "banner_timeout": self.timeout,
                "auth_timeout": self.timeout,
            }
            if self.password:
                connect_kwargs["password"] = self.password
            if self.key_filename:
                connect_kwargs["key_filename"] = self.key_filename

            self.client.connect(**connect_kwargs)
            return True, "SSH Connection Successful"
        except paramiko.AuthenticationException:
            return False, "การยืนยันตัวตนล้มเหลว: Username หรือ Password/SSH Key ไม่ถูกต้อง"
        except socket.timeout:
            return False, f"การเชื่อมต่อหมดเวลา (Timeout {self.timeout}s): ตรวจสอบ IP หรือ Firewall ขาเข้า"
        except Exception as e:
            return False, f"เกิดข้อผิดพลาดในการเชื่อมต่อ SSH: {str(e)}"

    def close(self):
        """Closes active SSH connection."""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None

    def exec_command(self, cmd: str, timeout: int = 10) -> Tuple[int, str, str]:
        """Executes remote command and returns (exit_status, stdout, stderr)."""
        if not self.client:
            is_ok, msg = self.connect()
            if not is_ok:
                return -1, "", msg

        try:
            stdin, stdout, stderr = self.client.exec_command(cmd, timeout=timeout)
            out = stdout.read().decode("utf-8", errors="ignore").strip()
            err = stderr.read().decode("utf-8", errors="ignore").strip()
            exit_code = stdout.channel.recv_exit_status()
            return exit_code, out, err
        except Exception as e:
            return -1, "", str(e)

    def run_full_audit(self) -> Dict[str, Any]:
        """
        Executes a complete Linux health & security baseline audit.
        Returns structured dictionary ready for GUI display and PDF report generation.
        """
        is_ok, conn_msg = self.connect()
        if not is_ok:
            return {
                "success": False,
                "error": conn_msg,
                "host": self.host,
                "port": self.port
            }

        try:
            audit_result: Dict[str, Any] = {
                "success": True,
                "host": self.host,
                "port": self.port,
                "user": self.user,
                "os_info": self._audit_os_info(),
                "uptime_load": self._audit_uptime_load(),
                "resources": self._audit_resources(),
                "disks": self._audit_storage(),
                "firewall": self._audit_firewall(),
                "patches": self._audit_patches(),
                "ssh_config": self._audit_ssh_config(),
                "services": self._audit_services(),
                "security_findings": []
            }

            # Calculate Security Score & Findings
            self._evaluate_security_compliance(audit_result)
            return audit_result
        finally:
            self.close()

    # --- Audit Sub-Methods ---

    def _audit_os_info(self) -> Dict[str, Any]:
        """Gathers OS distribution, kernel version, hostname and timezone."""
        _, os_rel, _ = self.exec_command("cat /etc/os-release")
        _, kernel, _ = self.exec_command("uname -r")
        _, arch, _ = self.exec_command("uname -m")
        _, hostname, _ = self.exec_command("hostname -f || hostname")
        _, tz, _ = self.exec_command("cat /etc/timezone 2>/dev/null || timedatectl | grep 'Time zone' || date +%Z")

        pretty_name = "Linux"
        for line in os_rel.splitlines():
            if line.startswith("PRETTY_NAME="):
                pretty_name = line.split("=", 1)[1].strip('"\'')
                break

        return {
            "distro": pretty_name,
            "kernel": kernel,
            "arch": arch,
            "hostname": hostname,
            "timezone": tz.strip()
        }

    def _audit_uptime_load(self) -> Dict[str, Any]:
        """Gathers system uptime and load averages."""
        _, uptime_str, _ = self.exec_command("uptime")
        load_1m, load_5m, load_15m = 0.0, 0.0, 0.0

        load_match = re.search(r"load average[s]?:\s*([\d\.]+),?\s*([\d\.]+),?\s*([\d\.]+)", uptime_str)
        if load_match:
            load_1m = float(load_match.group(1))
            load_5m = float(load_match.group(2))
            load_15m = float(load_match.group(3))

        return {
            "raw_uptime": uptime_str,
            "load_1m": load_1m,
            "load_5m": load_5m,
            "load_15m": load_15m
        }

    def _audit_resources(self) -> Dict[str, Any]:
        """Gathers CPU core count, RAM and Swap metrics."""
        _, cpu_cores_str, _ = self.exec_command("nproc || grep -c ^processor /proc/cpuinfo")
        _, free_str, _ = self.exec_command("free -m")

        cores = int(cpu_cores_str) if cpu_cores_str.isdigit() else 1
        ram_total, ram_used, ram_free = 0, 0, 0
        swap_total, swap_used = 0, 0

        for line in free_str.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                if parts[0].lower().startswith("mem:"):
                    ram_total = int(parts[1])
                    ram_used = int(parts[2])
                    ram_free = int(parts[3])
                elif parts[0].lower().startswith("swap:"):
                    swap_total = int(parts[1])
                    swap_used = int(parts[2])

        ram_pct = round((ram_used / ram_total * 100), 1) if ram_total > 0 else 0
        swap_pct = round((swap_used / swap_total * 100), 1) if swap_total > 0 else 0

        return {
            "cpu_cores": cores,
            "ram_total_mb": ram_total,
            "ram_used_mb": ram_used,
            "ram_free_mb": ram_free,
            "ram_pct": ram_pct,
            "swap_total_mb": swap_total,
            "swap_used_mb": swap_used,
            "swap_pct": swap_pct
        }

    def _audit_storage(self) -> List[Dict[str, Any]]:
        """Gathers storage partitions and usage percentages."""
        _, df_str, _ = self.exec_command("df -h -x tmpfs -x devtmpfs -x squashfs -x overlay")
        partitions = []

        for line in df_str.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 6:
                fs, size, used, avail, use_pct, mount = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
                pct_val = int(use_pct.rstrip("%")) if use_pct.rstrip("%").isdigit() else 0
                partitions.append({
                    "filesystem": fs,
                    "size": size,
                    "used": used,
                    "avail": avail,
                    "use_pct": pct_val,
                    "mount": mount,
                    "is_warning": pct_val >= 80,
                    "is_critical": pct_val >= 90
                })

        return partitions

    def _audit_firewall(self) -> Dict[str, Any]:
        """
        Audits firewall status across UFW, Firewalld, and IPTables.
        Crucial check for security assessment.
        """
        firewall_type = "None / Unknown"
        is_active = False
        status_detail = ""

        # 1. Check UFW (Ubuntu/Debian)
        code_ufw, ufw_out, _ = self.exec_command("which ufw >/dev/null && ufw status verbose")
        if code_ufw == 0 and "status:" in ufw_out.lower():
            firewall_type = "UFW (Uncomplicated Firewall)"
            if "status: active" in ufw_out.lower():
                is_active = True
                status_detail = "Active (เปิดใช้งานและมีกฎป้องกัน)"
            else:
                is_active = False
                status_detail = "INACTIVE (ปิดใช้งานอยู่! มีความเสี่ยง)"
            return {
                "type": firewall_type,
                "is_active": is_active,
                "status_detail": status_detail,
                "raw": ufw_out
            }

        # 2. Check Firewalld (RHEL/CentOS/Rocky/Alma)
        code_fwd, fwd_out, _ = self.exec_command("which firewall-cmd >/dev/null && firewall-cmd --state")
        if code_fwd == 0:
            firewall_type = "Firewalld"
            if "running" in fwd_out.lower():
                is_active = True
                status_detail = "Running (เปิดใช้งาน)"
            else:
                is_active = False
                status_detail = "Not running (ปิดใช้งานอยู่! มีความเสี่ยง)"
            return {
                "type": firewall_type,
                "is_active": is_active,
                "status_detail": status_detail,
                "raw": fwd_out
            }

        # 3. Check IPTables
        code_ipt, ipt_out, _ = self.exec_command("iptables -L -n 2>/dev/null | grep -E 'Chain (INPUT|FORWARD)'")
        if code_ipt == 0 and ipt_out:
            firewall_type = "IPTables"
            # Count rules in INPUT
            _, ipt_count, _ = self.exec_command("iptables -S INPUT 2>/dev/null | wc -l")
            rule_count = int(ipt_count) if ipt_count.isdigit() else 0
            if rule_count > 1:
                is_active = True
                status_detail = f"Active (IPTables มีกฎ {rule_count} ข้อ)"
            else:
                is_active = False
                status_detail = "No custom rules (เปิดพอร์ตทุกพอร์ต ไร้การกรอง)"
            return {
                "type": firewall_type,
                "is_active": is_active,
                "status_detail": status_detail,
                "raw": ipt_out
            }

        return {
            "type": "Not Detected",
            "is_active": False,
            "status_detail": "ไม่พบ Firewall ทำงานอยู่บนเครื่อง (ปิดการป้องกันทั้งหมด)",
            "raw": ""
        }

    def _audit_patches(self) -> Dict[str, Any]:
        """
        Audits pending OS updates and security patches.
        Checks APT (Debian/Ubuntu) or DNF/YUM (RHEL/CentOS).
        """
        total_updates = 0
        security_updates = 0
        details = []

        # 1. APT Package Manager
        code_apt, _, _ = self.exec_command("which apt >/dev/null")
        if code_apt == 0:
            _, apt_out, _ = self.exec_command("apt list --upgradable 2>/dev/null | grep -v 'Listing...' | head -n 50")
            lines = [l for l in apt_out.splitlines() if "/" in l]
            total_updates = len(lines)
            for line in lines:
                is_sec = "security" in line.lower()
                if is_sec:
                    security_updates += 1
                details.append({
                    "package": line.split("/")[0],
                    "info": line,
                    "is_security": is_sec
                })

            return {
                "pkg_manager": "APT",
                "total_upgrades": total_updates,
                "security_upgrades": security_updates,
                "status_text": (
                    "ระบบเป็นเวอร์ชันล่าสุด 100%" if total_updates == 0
                    else f"มีแพตช์รออัปเดต {total_updates} รายการ (แพตช์ความปลอดภัย: {security_updates} รายการ)"
                ),
                "packages_sample": details[:10]
            }

        # 2. DNF / YUM
        code_dnf, _, _ = self.exec_command("which dnf >/dev/null || which yum >/dev/null")
        if code_dnf == 0:
            cmd = "dnf check-update -q 2>/dev/null || yum check-update -q 2>/dev/null"
            _, dnf_out, _ = self.exec_command(f"{cmd} | head -n 50")
            lines = [l for l in dnf_out.splitlines() if len(l.split()) >= 3]
            total_updates = len(lines)
            return {
                "pkg_manager": "DNF/YUM",
                "total_upgrades": total_updates,
                "security_upgrades": 0,
                "status_text": (
                    "ระบบเป็นเวอร์ชันล่าสุด" if total_updates == 0
                    else f"มีแพตช์รออัปเดต {total_updates} รายการ"
                ),
                "packages_sample": [{"package": l.split()[0], "info": l, "is_security": False} for l in lines[:10]]
            }

        return {
            "pkg_manager": "Unknown",
            "total_upgrades": 0,
            "security_upgrades": 0,
            "status_text": "ไม่สามารถตรวจสอบตัวจัดการแพ็กเกจได้",
            "packages_sample": []
        }

    def _audit_ssh_config(self) -> Dict[str, Any]:
        """Audits SSH daemon security configuration."""
        _, sshd_grep, _ = self.exec_command(
            "grep -E '^(PermitRootLogin|PasswordAuthentication|Port)' /etc/ssh/sshd_config 2>/dev/null"
        )
        permit_root = "Unknown (default yes)"
        password_auth = "Unknown (default yes)"
        ssh_port = "22 (Default)"

        for line in sshd_grep.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                k, v = parts[0], parts[1]
                if k == "PermitRootLogin":
                    permit_root = v
                elif k == "PasswordAuthentication":
                    password_auth = v
                elif k == "Port":
                    ssh_port = v

        return {
            "permit_root_login": permit_root,
            "password_auth": password_auth,
            "configured_port": ssh_port,
            "is_root_login_disabled": permit_root.lower() in ["no", "prohibit-password"],
            "raw": sshd_grep
        }

    def _audit_services(self) -> List[Dict[str, Any]]:
        """Audits essential server daemon statuses."""
        target_services = [
            ("SSH Daemon", "sshd || ssh"),
            ("MySQL / MariaDB", "mysql || mariadb || mysqld"),
            ("Web Server (Nginx/Apache)", "nginx || apache2 || httpd"),
            ("Docker Engine", "docker"),
            ("Time Sync (Chrony/NTP)", "chrony || chronyd || ntp || systemd-timesyncd"),
            ("Cron Daemon", "cron || crond")
        ]
        results = []
        for name, svc_cmd in target_services:
            code, out, _ = self.exec_command(f"systemctl is-active {svc_cmd} 2>/dev/null")
            status = "active" if "active" in out.lower() else "inactive"
            results.append({
                "service": name,
                "status": status,
                "is_running": status == "active"
            })
        return results

    def _evaluate_security_compliance(self, audit: Dict[str, Any]):
        """Evaluates checklist criteria and calculates Overall Security Score (0-100)."""
        findings = []
        score = 100

        # 1. Firewall Check
        fw = audit.get("firewall", {})
        if fw.get("is_active"):
            findings.append({"category": "Firewall", "status": "PASS", "desc": f"Firewall เปิดใช้งาน ({fw.get('type')})"})
        else:
            findings.append({"category": "Firewall", "status": "CRITICAL", "desc": "Firewall ถูกปิดใช้งาน! เครื่องเปิดโล่งต่อการโจมตี"})
            score -= 25

        # 2. Patch & Security Updates Check
        pt = audit.get("patches", {})
        sec_up = pt.get("security_upgrades", 0)
        tot_up = pt.get("total_upgrades", 0)
        if sec_up > 0:
            findings.append({"category": "OS Patches", "status": "CRITICAL", "desc": f"พบแพตช์ความปลอดภัยที่ยังไม่อัปเดต {sec_up} รายการ"})
            score -= 20
        elif tot_up > 20:
            findings.append({"category": "OS Patches", "status": "WARNING", "desc": f"มีอัปเดตทั่วไปค้าง {tot_up} รายการ ควรทำการ Upgrade"})
            score -= 10
        else:
            findings.append({"category": "OS Patches", "status": "PASS", "desc": "แพตช์ระบบปฏิบัติการเป็นปัจจุบัน"})

        # 3. Disk Space Check
        disks = audit.get("disks", [])
        has_disk_crit = any(d.get("is_critical") for d in disks)
        has_disk_warn = any(d.get("is_warning") for d in disks)
        if has_disk_crit:
            findings.append({"category": "Disk Storage", "status": "CRITICAL", "desc": "พื้นที่ดิสก์ใกล้เต็ม (> 90%) เสี่ยงต่อระบบหยุดทำงาน"})
            score -= 20
        elif has_disk_warn:
            findings.append({"category": "Disk Storage", "status": "WARNING", "desc": "พื้นที่ดิสก์ใช้งานสูง (> 80%) ควรวางแผนขยายพื้นที่"})
            score -= 10
        else:
            findings.append({"category": "Disk Storage", "status": "PASS", "desc": "พื้นที่ดิสก์ทุกพาร์ติชันอยู่ในเกณฑ์ปกติ"})

        # 4. SSH Root Login Check
        ssh = audit.get("ssh_config", {})
        if ssh.get("is_root_login_disabled"):
            findings.append({"category": "SSH Hardening", "status": "PASS", "desc": "ปิด PermitRootLogin ป้องกันการ Brute-force ตรงเข้า Root"})
        else:
            findings.append({"category": "SSH Hardening", "status": "WARNING", "desc": "PermitRootLogin ยังเปิดใช้งาน ควรเปลี่ยนเป็น Key-only"})
            score -= 10

        # 5. Time Sync Service Check
        svcs = audit.get("services", [])
        time_sync = next((s for s in svcs if "Time Sync" in s["service"]), None)
        if time_sync and time_sync.get("is_running"):
            findings.append({"category": "Time Sync", "status": "PASS", "desc": "NTP / Chrony กำลังทำงาน เวลาเซิร์ฟเวอร์ตรง"})
        else:
            findings.append({"category": "Time Sync", "status": "WARNING", "desc": "ไม่พบเซอร์วิส Time Sync อาจส่งผลต่อเวลาในฐานข้อมูล"})
            score -= 5

        score = max(0, min(100, score))
        grade = "A+" if score >= 95 else "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "F"

        audit["security_score"] = score
        audit["security_grade"] = grade
        audit["security_findings"] = findings
