# -*- coding: utf-8 -*-
"""
Preset Linux Administration Commands Catalog.
Organized 1-click commands for sysadmins to run without memorizing complex syntax.
"""

from typing import List, Dict, Any

PRESET_ADMIN_COMMANDS: List[Dict[str, Any]] = [
    # Category 1: Disks & Storage
    {
        "category": "💾 ดิสก์ & พื้นที่จัดเก็บ",
        "commands": [
            {
                "title": "📊 สรุปพื้นที่ดิสก์ทุกพาร์ติชัน",
                "cmd": "df -h -x tmpfs -x devtmpfs -x squashfs",
                "desc": "ดูขนาด Used, Available และ Use % ของทุกไดรฟ์"
            },
            {
                "title": "🔍 10 โฟลเดอร์ที่กินพื้นที่มากสุดใน Root",
                "cmd": "du -ahx / 2>/dev/null | sort -rh | head -n 10",
                "desc": "ค้นหาจุดที่ไฟล์บวมเพื่อเคลียร์พื้นที่ฮาร์ดดิสก์"
            },
            {
                "title": "🗂️ ค้นหาไฟล์ขนาดใหญ่กว่า 100MB",
                "cmd": "find / -type f -size +100M -exec ls -lh {} + 2>/dev/null | awk '{print $9, \"(\" $5 \")\"}' | head -n 15",
                "desc": "ตรวจจับไฟล์ Log ขนาดใหญ่หรือไฟล์ Dump ที่ค้าง"
            },
            {
                "title": "💽 ดูโครงสร้างฮาร์ดดิสก์ (lsblk)",
                "cmd": "lsblk -o NAME,FSTYPE,SIZE,MOUNTPOINT,MODEL",
                "desc": "ดูรายชื่อ Block Devices, พาร์ติชัน และจุดเมานต์"
            },
        ]
    },
    # Category 2: CPU, RAM & Performance
    {
        "category": "⚡ ซีพียู & ประสิทธิภาพระบบ",
        "commands": [
            {
                "title": "🧠 10 โปรเซสที่กิน RAM สูงสุด",
                "cmd": "ps aux --sort=-%mem | head -n 11 | awk '{printf \"%-10s %-8s %-6s %-6s %s\\n\", $1, $2, $3, $4, $11}'",
                "desc": "ตรวจสอบว่าโปรแกรมใดกำลังดึงหน่วยความจำเซิร์ฟเวอร์"
            },
            {
                "title": "🚀 10 โปรเซสที่กิน CPU สูงสุด",
                "cmd": "ps aux --sort=-%cpu | head -n 11 | awk '{printf \"%-10s %-8s %-6s %-6s %s\\n\", $1, $2, $3, $4, $11}'",
                "desc": "ค้นหาโปรเซสที่ทำให้ CPU ทำงานหนักผิดปกติ"
            },
            {
                "title": "📈 ตรวจสอบ RAM & Swap (free -h)",
                "cmd": "free -h",
                "desc": "ดูหน่วยความจำที่ใช้งานจริง, Buff/Cache และ Swap"
            },
            {
                "title": "💻 ดูสเปก CPU และจำนวน Core",
                "cmd": "lscpu | grep -E 'Model name|CPU\\(s\\)|Thread|Core per socket|MHz'",
                "desc": "ดูรุ่นซีพียู, สถาปัตยกรรม และความเร็วสัญญาณนาฬิกา"
            },
            {
                "title": "⏱️ ตรวจสอบ Uptime & Load Average",
                "cmd": "uptime",
                "desc": "ดูระยะเวลาที่เซิร์ฟเวอร์เปิดใช้งาน และ Load 1m, 5m, 15m"
            },
        ]
    },
    # Category 3: Security & Firewall
    {
        "category": "🛡️ ไฟร์วอลล์ & ความปลอดภัย",
        "commands": [
            {
                "title": "🛡️ ตรวจสอบสถานะ Firewall (UFW / Firewalld)",
                "cmd": "ufw status verbose 2>/dev/null || firewall-cmd --list-all 2>/dev/null || iptables -L -n -v",
                "desc": "ดูว่าไฟร์วอลล์เปิดอยู่หรือไม่ และมีกฎอนุญาตพอร์ตใดบ้าง"
            },
            {
                "title": "🔌 ตรวจสอบพอร์ตที่เปิด Listening อยู่",
                "cmd": "ss -tulnp 2>/dev/null || netstat -tulnp",
                "desc": "ดูทุกพอร์ตที่เปิดรับการเชื่อมต่อพร้อมชื่อ Service"
            },
            {
                "title": "🚨 ตรวจจับการเดารหัสผ่าน SSH (Brute-force)",
                "cmd": "grep 'Failed password' /var/log/auth.log 2>/dev/null | tail -n 15 || journalctl -u ssh -u sshd -n 20 --no-pager | grep 'Failed' | tail -n 15",
                "desc": "ดู IP ที่พยายามสุ่มรหัสผ่านเข้ามาในเซิร์ฟเวอร์"
            },
            {
                "title": "👤 ดูประวัติการล็อกอิน 10 ครั้งล่าสุด",
                "cmd": "last -n 10",
                "desc": "ตรวจสอบผู้ใช้ที่เคยล็อกอินเข้ามา วันเวลา และ IP ปลายทาง"
            },
            {
                "title": "🔑 ตรวจสอบผู้ใช้ที่มีสิทธิ์ระดับ Root (UID 0)",
                "cmd": "awk -F: '($3 == \"0\") {print $1, \"(UID 0)\"}' /etc/passwd",
                "desc": "ตรวจสอบว่ามี User แอบแฝงที่ถือสิทธิ์ Root หรือไม่"
            },
        ]
    },
    # Category 4: Patches & Packages
    {
        "category": "📦 แพตช์ & อัปเดตระบบ",
        "commands": [
            {
                "title": "🔄 ดูรายการแพตช์อัปเดตที่ค้างอยู่ทั้งหมด",
                "cmd": "apt list --upgradable 2>/dev/null || dnf check-update",
                "desc": "ดูว่ามีโปรแกรมและแพ็กเกจใดรออัปเดตบ้าง"
            },
            {
                "title": "🛡️ กรองดูเฉพาะแพตช์ความปลอดภัย (Security)",
                "cmd": "apt list --upgradable 2>/dev/null | grep -i security || dnf check-update --security 2>/dev/null",
                "desc": "ดูเฉพาะแพตช์ที่มีผลต่อช่องโหว่ความปลอดภัยระดับวิกฤต"
            },
            {
                "title": "♻️ อัปเดตแคตตาล็อกแพ็กเกจ (apt update)",
                "cmd": "apt update 2>/dev/null || dnf makecache",
                "desc": "ดึงข้อมูลแพตช์ล่าสุดจาก Repository แม่ข่าย"
            },
        ]
    },
    # Category 5: Services & Logs
    {
        "category": "⚙️ บริการ & บันทึกข้อผิดพลาด",
        "commands": [
            {
                "title": "🟢 ดู Services ที่กำลังทำงาน (Running)",
                "cmd": "systemctl list-units --type=service --state=running --no-pager | head -n 25",
                "desc": "ดูรายชื่อ Systemd Services ที่ Active อยู่ในปัจจุบัน"
            },
            {
                "title": "❌ ตรวจสอบ Services ที่ Crash / ล้มเหลว (Failed)",
                "cmd": "systemctl list-units --type=service --state=failed --no-pager",
                "desc": "ค้นหา Service ที่สตาร์ตไม่ติดเพื่อแก้ไขปัญหา"
            },
            {
                "title": "📝 ดู System Error Log ระดับวิกฤตล่าสุด",
                "cmd": "journalctl -p 3 -xb -n 20 --no-pager",
                "desc": "ดูเฉพาะ Log Error / Critical ที่เกิดขึ้นในรอบการบูตนี้"
            },
            {
                "title": "🕒 ตรวจสอบการซิงค์เวลาแม่ข่าย (NTP/Chrony)",
                "cmd": "timedatectl status",
                "desc": "ดูว่าเวลาเดินตรงและซิงค์กับ NTP Server ถูกต้องหรือไม่"
            },
            {
                "title": "🌐 ดู IP Address และ Network Interfaces",
                "cmd": "ip -br addr show || ifconfig",
                "desc": "ดูการตั้งค่า IP Address และ Mac Address ของการ์ดแลนทุกใบ"
            },
            {
                "title": "⏰ ดูตารางงานอัตโนมัติ (Crontab)",
                "cmd": "crontab -l 2>/dev/null; echo '--- System Cron ---'; ls -la /etc/cron.*",
                "desc": "ดูงานอัตโนมัติที่ถูกตั้งเวลาไว้ในเซิร์ฟเวอร์"
            },
        ]
    }
]
