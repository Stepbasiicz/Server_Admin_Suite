# -*- coding: utf-8 -*-
"""
Network Diagnostic Module.
Provides high-performance Ping, Traceroute, and Multi-Threaded Port Scanner.
"""

import sys
import os
import re
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Callable

COMMON_PORTS_INFO = {
    21: {"name": "FTP", "desc": "File Transfer (Cleartext)", "risk": "Medium"},
    22: {"name": "SSH", "desc": "Secure Shell Remote Admin", "risk": "Normal"},
    23: {"name": "Telnet", "desc": "Telnet (Insecure Cleartext)", "risk": "High"},
    25: {"name": "SMTP", "desc": "Mail Transfer Protocol", "risk": "Low"},
    53: {"name": "DNS", "desc": "Domain Name System", "risk": "Normal"},
    80: {"name": "HTTP", "desc": "Web Server (Plaintext)", "risk": "Low"},
    110: {"name": "POP3", "desc": "Post Office Protocol v3", "risk": "Low"},
    143: {"name": "IMAP", "desc": "Internet Message Access", "risk": "Low"},
    443: {"name": "HTTPS", "desc": "Web Server (Encrypted TLS)", "risk": "Normal"},
    3306: {"name": "MySQL", "desc": "MySQL / MariaDB Database", "risk": "High (If public)"},
    5432: {"name": "PostgreSQL", "desc": "PostgreSQL Database", "risk": "High (If public)"},
    6379: {"name": "Redis", "desc": "Redis In-Memory Key-Value", "risk": "High (If public)"},
    8080: {"name": "HTTP-Alt", "desc": "Alternative Web / Proxy", "risk": "Low"},
    8443: {"name": "HTTPS-Alt", "desc": "Alternative Secure Web", "risk": "Normal"}
}


class NetworkDiagnostics:
    """Network diagnostic tests for server reachability and port posture."""

    @staticmethod
    def ping(host: str, count: int = 4, timeout_ms: int = 2000) -> Dict[str, Any]:
        """
        Executes ping command and returns detailed latency & loss metrics.
        """
        host = host.strip()
        result: Dict[str, Any] = {
            "host": host,
            "success": False,
            "packets_sent": count,
            "packets_received": 0,
            "packet_loss_pct": 100,
            "avg_ms": 0.0,
            "min_ms": 0.0,
            "max_ms": 0.0,
            "status_text": "Host Unreachable",
            "raw_output": ""
        }

        if not host:
            result["status_text"] = "ระบุ Host ไม่ถูกต้อง"
            return result

        try:
            if sys.platform == "win32":
                cmd = ["ping", "-n", str(count), "-w", str(timeout_ms), host]
            else:
                cmd = ["ping", "-c", str(count), "-W", str(max(1, timeout_ms // 1000)), host]

            p = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=0x08000000 if sys.platform == "win32" else 0,
                timeout=(count * (timeout_ms / 1000.0)) + 4
            )
            raw = p.stdout
            result["raw_output"] = raw

            if sys.platform == "win32":
                # Parse Packets: Sent = X, Received = Y, Lost = Z (N% loss)
                loss_match = re.search(r"Lost = \d+ \((\d+)% loss\)", raw, re.IGNORECASE)
                recv_match = re.search(r"Received = (\d+)", raw, re.IGNORECASE)
                if recv_match:
                    result["packets_received"] = int(recv_match.group(1))
                if loss_match:
                    result["packet_loss_pct"] = int(loss_match.group(1))

                # Parse Minimum = Xms, Maximum = Yms, Average = Zms
                rtt_match = re.search(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms", raw, re.IGNORECASE)
                if rtt_match:
                    result["min_ms"] = float(rtt_match.group(1))
                    result["max_ms"] = float(rtt_match.group(2))
                    result["avg_ms"] = float(rtt_match.group(3))
                    result["success"] = result["packets_received"] > 0
            else:
                loss_match = re.search(r"(\d+)% packet loss", raw)
                if loss_match:
                    result["packet_loss_pct"] = int(loss_match.group(1))
                    result["packets_received"] = count - int(count * result["packet_loss_pct"] / 100)
                rtt_match = re.search(r"rtt min/avg/max/mdev = ([\d\.]+)/([\d\.]+)/([\d\.]+)", raw)
                if rtt_match:
                    result["min_ms"] = float(rtt_match.group(1))
                    result["avg_ms"] = float(rtt_match.group(2))
                    result["max_ms"] = float(rtt_match.group(3))
                    result["success"] = True

            if result["success"]:
                avg = result["avg_ms"]
                if avg <= 30:
                    result["status_text"] = f"ยอดเยี่ยม (Latency: {avg:.1f} ms)"
                elif avg <= 100:
                    result["status_text"] = f"ปกติ (Latency: {avg:.1f} ms)"
                else:
                    result["status_text"] = f"ช้ากว่าเกณฑ์ (Latency: {avg:.1f} ms)"
            else:
                result["status_text"] = "ติดต่อไม่ได้ (Timeout / Packet Loss 100%)"

        except Exception as e:
            result["status_text"] = f"เกิดข้อผิดพลาด: {str(e)}"

        return result

    @staticmethod
    def traceroute(
        host: str,
        max_hops: int = 20,
        timeout_ms: int = 2000,
        hop_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes traceroute and parses hop by hop with real-time callback.
        """
        host = host.strip()
        hops: List[Dict[str, Any]] = []

        if not host:
            return hops

        try:
            if sys.platform == "win32":
                cmd = ["tracert", "-d", "-h", str(max_hops), "-w", str(timeout_ms), host]
            else:
                cmd = ["traceroute", "-n", "-m", str(max_hops), "-w", str(max(1, timeout_ms // 1000)), host]

            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=0x08000000 if sys.platform == "win32" else 0
            )

            for line in p.stdout:
                line_clean = line.strip()
                if not line_clean:
                    continue

                # Match Windows format: "  1    <1 ms    <1 ms    <1 ms  192.168.1.1"
                hop_match = re.match(r"^\s*(\d+)\s+([\d\*\<\s\w]+)\s+([\d\.\:\*a-fA-F]+)$", line_clean)
                if hop_match:
                    hop_num = int(hop_match.group(1))
                    rtt_str = hop_match.group(2).strip()
                    ip_addr = hop_match.group(3).strip()

                    hop_data = {
                        "hop": hop_num,
                        "ip": ip_addr,
                        "rtt_info": rtt_str,
                        "raw_line": line_clean
                    }
                    hops.append(hop_data)
                    if hop_callback:
                        hop_callback(hop_data)

            p.wait()
        except Exception as e:
            err_hop = {"hop": 0, "ip": "ERROR", "rtt_info": str(e), "raw_line": str(e)}
            hops.append(err_hop)
            if hop_callback:
                hop_callback(err_hop)

        return hops

    @staticmethod
    def scan_ports(
        host: str,
        ports: Optional[List[int]] = None,
        timeout: float = 0.8,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Multi-threaded Port Scanner checking if ports are open, closed, or filtered.
        """
        host = host.strip()
        if ports is None:
            ports = list(COMMON_PORTS_INFO.keys())

        results: List[Dict[str, Any]] = []

        def _check_port(port: int) -> Dict[str, Any]:
            info = COMMON_PORTS_INFO.get(port, {"name": "Custom", "desc": f"Port {port}", "risk": "Normal"})
            status = "CLOSED"
            latency_ms = 0.0

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            t0 = time.time()
            try:
                res = s.connect_ex((host, port))
                latency_ms = (time.time() - t0) * 1000.0
                if res == 0:
                    status = "OPEN"
                else:
                    status = "CLOSED"
            except socket.timeout:
                status = "FILTERED/TIMEOUT"
            except Exception:
                status = "ERROR"
            finally:
                s.close()

            item = {
                "port": port,
                "service": info["name"],
                "description": info["desc"],
                "status": status,
                "risk": info["risk"],
                "latency_ms": round(latency_ms, 1)
            }
            if progress_callback:
                progress_callback(item)
            return item

        with ThreadPoolExecutor(max_workers=min(20, len(ports))) as executor:
            futures = [executor.submit(_check_port, p) for p in ports]
            for f in as_completed(futures):
                results.append(f.result())

        # Sort by port number
        results.sort(key=lambda x: x["port"])
        return results
