# -*- coding: utf-8 -*-
"""
Main GUI Window for Soft4U Server Admin & Security Audit Suite.
Developed with CustomTkinter, Dynamic Thai Font, Dark/Light Mode,
Masked Sensitive Inputs, 1-Click Linux Admin Toolbox, and ThreadPoolExecutor.
"""

import os
import sys
import time
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

from version import APP_TITLE, APP_VERSION
from app.core.config_manager import ConfigManager
from app.core.font_manager import FontManager
from app.core.license_manager import LicenseManager
from app.core.updater import AutoUpdater
from app.modules.network_diagnostics import NetworkDiagnostics
from app.modules.linux_ssh_auditor import LinuxSSHAuditor
from app.modules.mysql_auditor import MySQLAuditor
from app.modules.pdf_report_generator import PDFReportGenerator
from app.modules.admin_commands import PRESET_ADMIN_COMMANDS
from app.ui.license_dialog import LicenseDialog


class ServerAdminApp(ctk.CTk):
    """Enterprise Desktop GUI for Server Management & Security Audits."""

    def __init__(self):
        super().__init__()

        # 1. Core Config & Managers
        self.config_mgr = ConfigManager.get_instance()
        self.font_fam = FontManager.resolve_best_font(self)
        self.license_mgr = LicenseManager(self.config_mgr)
        self.updater = AutoUpdater()
        self.pdf_generator = PDFReportGenerator(output_dir="reports")
        self.executor = ThreadPoolExecutor(max_workers=5)

        # 2. Window Setup
        self.title(f"{APP_TITLE} (v{APP_VERSION})")
        self.geometry("1220x800")
        self.minsize(1100, 720)

        theme = self.config_mgr.get_setting("theme", "Dark")
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")

        # 3. State Variables
        self.current_server_id = tk.StringVar()
        self.status_var = tk.StringVar(value="พร้อมทำงาน (Ready)")
        self.audit_cache: Dict[str, Any] = {}

        # 4. Build Layout
        self._build_sidebar()
        self._build_main_content()
        self._load_servers_into_ui()
        self._refresh_license_badge()

    def _build_sidebar(self):
        """Left navigation sidebar."""
        self.sidebar = ctk.CTkFrame(self, width=230, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Brand Title
        lbl_brand = ctk.CTkLabel(
            self.sidebar,
            text="🛡️ Server Admin",
            font=ctk.CTkFont(family=self.font_fam, size=18, weight="bold")
        )
        lbl_brand.pack(padx=16, pady=(16, 2))

        lbl_sub = ctk.CTkLabel(
            self.sidebar,
            text=f"Security & Audit Suite v{APP_VERSION}",
            font=ctk.CTkFont(family=self.font_fam, size=10),
            text_color="gray"
        )
        lbl_sub.pack(padx=16, pady=(0, 12))

        # Server Selector Dropdown
        lbl_sel = ctk.CTkLabel(
            self.sidebar,
            text="เลือกเซิร์ฟเวอร์เป้าหมาย:",
            font=ctk.CTkFont(family=self.font_fam, size=11, weight="bold")
        )
        lbl_sel.pack(padx=16, pady=(2, 2), anchor="w")

        self.server_menu = ctk.CTkOptionMenu(
            self.sidebar,
            variable=self.current_server_id,
            values=["(ยังไม่มีเซิร์ฟเวอร์)"],
            command=self._on_server_selected,
            font=ctk.CTkFont(family=self.font_fam, size=12)
        )
        self.server_menu.pack(padx=14, pady=(0, 12), fill="x")

        # Navigation Buttons
        self.nav_btns: Dict[str, ctk.CTkButton] = {}
        tabs = [
            ("dashboard", "📊 แดชบอร์ดภาพรวม", self._show_tab_dashboard),
            ("network", "🌐 ทดสอบ Network / Port", self._show_tab_network),
            ("linux", "🐧 Linux Health & Tools", self._show_tab_linux),
            ("mysql", "🗄️ MySQL Database", self._show_tab_mysql),
            ("pdf", "📄 ส่งออก PDF Audit", self._show_tab_pdf),
            ("settings", "⚙️ จัดการ Server & Vault", self._show_tab_settings),
        ]

        for tab_id, tab_label, cmd in tabs:
            btn = ctk.CTkButton(
                self.sidebar,
                text=tab_label,
                anchor="w",
                font=ctk.CTkFont(family=self.font_fam, size=12),
                command=cmd,
                height=34,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray75", "gray25")
            )
            btn.pack(padx=12, pady=2, fill="x")
            self.nav_btns[tab_id] = btn

        # Bottom Sidebar Utilities
        frm_bot = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        frm_bot.pack(side="bottom", fill="x", padx=12, pady=12)

        # 1. License Key Button
        btn_license = ctk.CTkButton(
            frm_bot,
            text="🔑 ลงทะเบียน License Key",
            command=self._open_license_dialog,
            font=ctk.CTkFont(family=self.font_fam, size=11),
            fg_color="#4A5568",
            hover_color="#2D3748",
            height=30
        )
        btn_license.pack(fill="x", pady=(0, 6))

        # 2. Check Updates Button
        btn_update = ctk.CTkButton(
            frm_bot,
            text="🔄 ตรวจสอบอัปเดต (Updates)",
            command=self._check_updates_async,
            font=ctk.CTkFont(family=self.font_fam, size=11),
            fg_color="#2B6CB0",
            hover_color="#2C5282",
            height=30
        )
        btn_update.pack(fill="x", pady=(0, 8))

        # 3. Quick Theme Toggle
        self.theme_switch = ctk.CTkSegmentedButton(
            frm_bot,
            values=["Dark", "Light"],
            command=self._change_theme,
            font=ctk.CTkFont(family=self.font_fam, size=11)
        )
        self.theme_switch.set(self.config_mgr.get_setting("theme", "Dark"))
        self.theme_switch.pack(fill="x", pady=(0, 8))

        # 4. Trial / License Badge
        self.lbl_trial = ctk.CTkLabel(
            frm_bot,
            text="⏳ กำลังตรวจสอบสิทธิ์...",
            font=ctk.CTkFont(family=self.font_fam, size=10),
            text_color="gray"
        )
        self.lbl_trial.pack(anchor="w")

    def _build_main_content(self):
        """Top bar and Tab Container."""
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True)

        # Header status bar
        self.top_bar = ctk.CTkFrame(self.content_area, height=38, corner_radius=0)
        self.top_bar.pack(fill="x")
        self.lbl_status = ctk.CTkLabel(
            self.top_bar,
            textvariable=self.status_var,
            font=ctk.CTkFont(family=self.font_fam, size=11),
            text_color="gray"
        )
        self.lbl_status.pack(side="left", padx=16)

        # View container
        self.view_container = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.view_container.pack(fill="both", expand=True, padx=14, pady=10)

        # Tabs dict
        self.tabs = {}
        self._init_all_tabs()
        self._show_tab_dashboard()

    def _init_all_tabs(self):
        self._init_dashboard_tab()
        self._init_network_tab()
        self._init_linux_tab()
        self._init_mysql_tab()
        self._init_pdf_tab()
        self._init_settings_tab()

    # --- TAB 1: DASHBOARD ---
    def _init_dashboard_tab(self):
        tab = ctk.CTkScrollableFrame(self.view_container, fg_color="transparent")
        self.tabs["dashboard"] = tab

        # Title Card
        card_top = ctk.CTkFrame(tab, corner_radius=8)
        card_top.pack(fill="x", pady=(0, 10), padx=4, ipady=8)

        ctk.CTkLabel(
            card_top,
            text="ศูนย์ตรวจสอบและดูแลความปลอดภัยระบบเซิร์ฟเวอร์ (Admin Command Center)",
            font=ctk.CTkFont(family=self.font_fam, size=15, weight="bold")
        ).pack(anchor="w", padx=16, pady=(4, 2))

        ctk.CTkLabel(
            card_top,
            text="รวมศูนย์ Ping, Tracert, Scan Port, Linux Health, Firewall, Patch Update และ MySQL ในที่เดียว",
            font=ctk.CTkFont(family=self.font_fam, size=11),
            text_color="gray"
        ).pack(anchor="w", padx=16, pady=(0, 6))

        # Action Buttons
        frm_actions = ctk.CTkFrame(card_top, fg_color="transparent")
        frm_actions.pack(fill="x", padx=16, pady=4)

        btn_run_all = ctk.CTkButton(
            frm_actions,
            text="🚀 รันการตรวจสอบแบบละเอียดครบวงจร (Run Full Audit)",
            command=self._run_full_audit_async,
            font=ctk.CTkFont(family=self.font_fam, size=12, weight="bold"),
            fg_color="#2B6CB0",
            hover_color="#2C5282",
            height=36
        )
        btn_run_all.pack(side="left", padx=(0, 10))

        btn_gen_pdf = ctk.CTkButton(
            frm_actions,
            text="📄 สร้างรายงาน PDF สรุปผลความปลอดภัย",
            command=self._export_pdf_direct,
            font=ctk.CTkFont(family=self.font_fam, size=12),
            fg_color="#38A169",
            hover_color="#276749",
            height=36
        )
        btn_gen_pdf.pack(side="left")

        # 4 Metric Cards
        frm_cards = ctk.CTkFrame(tab, fg_color="transparent")
        frm_cards.pack(fill="x", pady=6)

        self.card_ping = self._create_metric_card(frm_cards, "🌐 Network Ping", "รอการทดสอบ", "#4A5568")
        self.card_ping.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self.card_os = self._create_metric_card(frm_cards, "🐧 Linux Status", "รอเชื่อมต่อ SSH", "#4A5568")
        self.card_os.pack(side="left", fill="both", expand=True, padx=6)

        self.card_fw = self._create_metric_card(frm_cards, "🛡️ Firewall Posture", "ยังไม่ตรวจสอบ", "#4A5568")
        self.card_fw.pack(side="left", fill="both", expand=True, padx=6)

        self.card_db = self._create_metric_card(frm_cards, "🗄️ MySQL Database", "ยังไม่ตรวจสอบ", "#4A5568")
        self.card_db.pack(side="left", fill="both", expand=True, padx=(6, 0))

        # Real-time Activity Log
        lbl_log = ctk.CTkLabel(
            tab,
            text="บันทึกผลการตรวจสอบล่าสุด (Live Audit Telemetry Log):",
            font=ctk.CTkFont(family=self.font_fam, size=12, weight="bold")
        )
        lbl_log.pack(anchor="w", padx=4, pady=(12, 4))

        self.txt_dash_log = ctk.CTkTextbox(
            tab,
            height=280,
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=6
        )
        self.txt_dash_log.pack(fill="both", expand=True, padx=4, pady=(0, 10))
        self.txt_dash_log.insert("end", "[SYSTEM READY] เลือกเซิร์ฟเวอร์แล้วกด 'รันการตรวจสอบแบบละเอียด' เพื่อเริ่มต้น...\n")

    def _create_metric_card(self, parent, title: str, default_val: str, color_tag: str):
        card = ctk.CTkFrame(parent, corner_radius=8)
        lbl_t = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family=self.font_fam, size=11, weight="bold"), text_color="gray")
        lbl_t.pack(anchor="w", padx=12, pady=(8, 2))
        lbl_v = ctk.CTkLabel(card, text=default_val, font=ctk.CTkFont(family=self.font_fam, size=13, weight="bold"), text_color=color_tag)
        lbl_v.pack(anchor="w", padx=12, pady=(0, 8))
        card.value_label = lbl_v
        return card

    # --- TAB 2: NETWORK DIAGNOSTICS ---
    def _init_network_tab(self):
        tab = ctk.CTkScrollableFrame(self.view_container, fg_color="transparent")
        self.tabs["network"] = tab

        card_ctrl = ctk.CTkFrame(tab, corner_radius=8)
        card_ctrl.pack(fill="x", pady=(0, 10), padx=4, ipady=6)

        ctk.CTkLabel(
            card_ctrl,
            text="เครื่องมือทดสอบระบบเครือข่าย (Ping & Visual Traceroute)",
            font=ctk.CTkFont(family=self.font_fam, size=14, weight="bold")
        ).pack(anchor="w", padx=14, pady=(6, 6))

        frm_input = ctk.CTkFrame(card_ctrl, fg_color="transparent")
        frm_input.pack(fill="x", padx=14, pady=4)

        ctk.CTkLabel(frm_input, text="Target IP / Host:", font=ctk.CTkFont(family=self.font_fam, size=12)).pack(side="left", padx=(0, 8))
        self.entry_net_host = ctk.CTkEntry(frm_input, width=200, font=ctk.CTkFont(family="Consolas", size=12))
        self.entry_net_host.pack(side="left", padx=(0, 10))

        btn_ping = ctk.CTkButton(
            frm_input,
            text="⚡ ทดสอบ Ping",
            command=self._run_ping_async,
            font=ctk.CTkFont(family=self.font_fam, size=12, weight="bold"),
            width=110
        )
        btn_ping.pack(side="left", padx=(0, 6))

        btn_trace = ctk.CTkButton(
            frm_input,
            text="🗺️ รัน Traceroute",
            command=self._run_tracert_async,
            font=ctk.CTkFont(family=self.font_fam, size=12),
            width=120
        )
        btn_trace.pack(side="left", padx=(0, 6))

        btn_scan = ctk.CTkButton(
            frm_input,
            text="🔍 สแกนพอร์ตมาตรฐาน",
            command=self._run_port_scan_async,
            font=ctk.CTkFont(family=self.font_fam, size=12),
            fg_color="#D69E2E",
            hover_color="#B7791F",
            width=150
        )
        btn_scan.pack(side="left")

        # Network Output Console
        lbl_out = ctk.CTkLabel(tab, text="ผลการทดสอบ Network & Port:", font=ctk.CTkFont(family=self.font_fam, size=12, weight="bold"))
        lbl_out.pack(anchor="w", padx=4, pady=(8, 4))

        self.txt_net_log = ctk.CTkTextbox(tab, height=360, font=ctk.CTkFont(family="Consolas", size=11), corner_radius=6)
        self.txt_net_log.pack(fill="both", expand=True, padx=4, pady=(0, 8))

    # --- TAB 3: LINUX AUDIT & 1-CLICK COMMAND TOOLBOX ---
    def _init_linux_tab(self):
        tab = ctk.CTkScrollableFrame(self.view_container, fg_color="transparent")
        self.tabs["linux"] = tab

        # Top Control Card
        card_top = ctk.CTkFrame(tab, corner_radius=8)
        card_top.pack(fill="x", pady=(0, 8), padx=4, ipady=6)

        ctk.CTkLabel(
            card_top,
            text="🐧 ตรวจสอบสุขภาพและดูแล Linux Server ผ่าน SSH",
            font=ctk.CTkFont(family=self.font_fam, size=15, weight="bold")
        ).pack(anchor="w", padx=14, pady=(4, 2))

        frm_ssh_btn = ctk.CTkFrame(card_top, fg_color="transparent")
        frm_ssh_btn.pack(fill="x", padx=14, pady=4)

        btn_audit_linux = ctk.CTkButton(
            frm_ssh_btn,
            text="🔎 ดึงข้อมูลและตรวจสอบ Linux ฉบับเต็ม (Inspect All)",
            command=self._run_linux_audit_async,
            font=ctk.CTkFont(family=self.font_fam, size=12, weight="bold"),
            fg_color="#2B6CB0",
            height=34
        )
        btn_audit_linux.pack(side="left", padx=(0, 10))

        # 4 Structured Summary Cards for Linux
        frm_l_metrics = ctk.CTkFrame(tab, fg_color="transparent")
        frm_l_metrics.pack(fill="x", pady=(0, 8))

        self.card_l_os = self._create_metric_card(frm_l_metrics, "ระบบปฏิบัติการ (OS)", "ยังไม่ดึงข้อมูล", "#4A5568")
        self.card_l_os.pack(side="left", fill="both", expand=True, padx=(0, 4))

        self.card_l_cpu = self._create_metric_card(frm_l_metrics, "CPU & Load", "-", "#4A5568")
        self.card_l_cpu.pack(side="left", fill="both", expand=True, padx=4)

        self.card_l_ram = self._create_metric_card(frm_l_metrics, "RAM / Swap", "-", "#4A5568")
        self.card_l_ram.pack(side="left", fill="both", expand=True, padx=4)

        self.card_l_fw = self._create_metric_card(frm_l_metrics, "Firewall & Patch", "-", "#4A5568")
        self.card_l_fw.pack(side="left", fill="both", expand=True, padx=(4, 0))

        # ======================================================================
        # 🌟 1-CLICK LINUX ADMIN COMMAND TOOLBOX (ไม่ต้องจำคำสั่ง/ไม่ต้องพิมพ์!)
        # ======================================================================
        card_tools = ctk.CTkFrame(tab, corner_radius=8, border_width=1, border_color=("gray75", "gray30"))
        card_tools.pack(fill="x", pady=8, padx=4, ipady=6)

        ctk.CTkLabel(
            card_tools,
            text="🧰 คลังคำสั่ง Linux ด่วนสำหรับ Admin (คลิกเพื่อรันได้ทันที ไม่ต้องจำคำสั่ง)",
            font=ctk.CTkFont(family=self.font_fam, size=13, weight="bold"),
            text_color="#38A169"
        ).pack(anchor="w", padx=14, pady=(6, 4))

        # Sub-tab selector for categories
        self.cmd_category_tabview = ctk.CTkTabview(card_tools, height=140)
        self.cmd_category_tabview.pack(fill="x", padx=10, pady=(0, 6))

        for cat in PRESET_ADMIN_COMMANDS:
            cat_name = cat["category"]
            t_page = self.cmd_category_tabview.add(cat_name)

            # Flow of quick buttons
            frm_btns = ctk.CTkFrame(t_page, fg_color="transparent")
            frm_btns.pack(fill="both", expand=True, padx=4, pady=4)

            for i, cmd_info in enumerate(cat["commands"]):
                btn_cmd = ctk.CTkButton(
                    frm_btns,
                    text=cmd_info["title"],
                    command=lambda c=cmd_info["cmd"], desc=cmd_info["desc"]: self._run_preset_command(c, desc),
                    font=ctk.CTkFont(family=self.font_fam, size=11),
                    height=28,
                    fg_color=("gray85", "gray25"),
                    hover_color="#2B6CB0",
                    text_color=("gray10", "gray90")
                )
                row, col = divmod(i, 3)
                btn_cmd.grid(row=row, column=col, sticky="w", padx=6, pady=4)

        # Custom Command Input row
        frm_cmd_in = ctk.CTkFrame(tab, corner_radius=8)
        frm_cmd_in.pack(fill="x", pady=6, padx=4, ipady=4)

        ctk.CTkLabel(
            frm_cmd_in,
            text="หรือพิมพ์คำสั่ง Linux เอง:",
            font=ctk.CTkFont(family=self.font_fam, size=11, weight="bold")
        ).pack(anchor="w", padx=14, pady=(2, 2))

        frm_row = ctk.CTkFrame(frm_cmd_in, fg_color="transparent")
        frm_row.pack(fill="x", padx=14, pady=(0, 4))

        self.entry_linux_cmd = ctk.CTkEntry(
            frm_row,
            placeholder_text="ระบุคำสั่งที่ต้องการรัน เช่น df -h, ufw status, free -m...",
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.entry_linux_cmd.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_linux_cmd.bind("<Return>", lambda e: self._exec_custom_linux_cmd_async())

        btn_run_cmd = ctk.CTkButton(
            frm_row,
            text="ส่งคำสั่ง (Exec)",
            command=self._exec_custom_linux_cmd_async,
            width=110,
            font=ctk.CTkFont(family=self.font_fam, size=12)
        )
        btn_run_cmd.pack(side="right")

        # Linux Output Terminal Box
        self.txt_linux_log = ctk.CTkTextbox(tab, height=360, font=ctk.CTkFont(family="Consolas", size=11), corner_radius=6)
        self.txt_linux_log.pack(fill="both", expand=True, padx=4, pady=(6, 8))

    # --- TAB 4: MYSQL AUDIT ---
    def _init_mysql_tab(self):
        tab = ctk.CTkScrollableFrame(self.view_container, fg_color="transparent")
        self.tabs["mysql"] = tab

        card_top = ctk.CTkFrame(tab, corner_radius=8)
        card_top.pack(fill="x", pady=(0, 8), padx=4, ipady=6)

        ctk.CTkLabel(
            card_top,
            text="🗄️ ตรวจสอบฐานข้อมูล MySQL / MariaDB (Health & Schemas)",
            font=ctk.CTkFont(family=self.font_fam, size=15, weight="bold")
        ).pack(anchor="w", padx=14, pady=(4, 2))

        frm_btn = ctk.CTkFrame(card_top, fg_color="transparent")
        frm_btn.pack(fill="x", padx=14, pady=4)

        btn_db_test = ctk.CTkButton(
            frm_btn,
            text="🔌 ทดสอบเชื่อมต่อ MySQL",
            command=self._run_mysql_test_async,
            font=ctk.CTkFont(family=self.font_fam, size=12),
            width=160
        )
        btn_db_test.pack(side="left", padx=(0, 8))

        btn_db_full = ctk.CTkButton(
            frm_btn,
            text="📊 ดึงขนาดทุกฐานข้อมูล & เช็คความปลอดภัย",
            command=self._run_mysql_audit_async,
            font=ctk.CTkFont(family=self.font_fam, size=12, weight="bold"),
            fg_color="#2B6CB0",
            width=260
        )
        btn_db_full.pack(side="left", padx=(0, 8))

        # MySQL Metrics Cards
        frm_my_metrics = ctk.CTkFrame(tab, fg_color="transparent")
        frm_my_metrics.pack(fill="x", pady=(0, 8))

        self.card_my_ver = self._create_metric_card(frm_my_metrics, "เวอร์ชัน MySQL", "ยังไม่ตรวจสอบ", "#4A5568")
        self.card_my_ver.pack(side="left", fill="both", expand=True, padx=(0, 4))

        self.card_my_up = self._create_metric_card(frm_my_metrics, "Uptime", "-", "#4A5568")
        self.card_my_up.pack(side="left", fill="both", expand=True, padx=4)

        self.card_my_bp = self._create_metric_card(frm_my_metrics, "Buffer Pool", "-", "#4A5568")
        self.card_my_bp.pack(side="left", fill="both", expand=True, padx=4)

        self.card_my_conn = self._create_metric_card(frm_my_metrics, "การเชื่อมต่อ (Threads)", "-", "#4A5568")
        self.card_my_conn.pack(side="left", fill="both", expand=True, padx=(4, 0))

        # Output Box
        self.txt_mysql_log = ctk.CTkTextbox(tab, height=380, font=ctk.CTkFont(family="Consolas", size=11), corner_radius=6)
        self.txt_mysql_log.pack(fill="both", expand=True, padx=4, pady=(4, 8))

    # --- TAB 5: PDF REPORT ---
    def _init_pdf_tab(self):
        tab = ctk.CTkScrollableFrame(self.view_container, fg_color="transparent")
        self.tabs["pdf"] = tab

        card = ctk.CTkFrame(tab, corner_radius=8)
        card.pack(fill="x", pady=(0, 10), padx=4, ipady=10)

        ctk.CTkLabel(
            card,
            text="📄 สร้างรายงานผลการประเมินความปลอดภัย Server (PDF Audit Report)",
            font=ctk.CTkFont(family=self.font_fam, size=15, weight="bold")
        ).pack(anchor="w", padx=16, pady=(4, 2))

        ctk.CTkLabel(
            card,
            text="จัดทำเอกสาร PDF A4 มาตรฐานสำหรับเสนอผู้บริหาร / กรรมการตรวจสอบ IT Audit (HA, ISO 27001)",
            font=ctk.CTkFont(family=self.font_fam, size=11),
            text_color="gray"
        ).pack(anchor="w", padx=16, pady=(0, 10))

        frm_actions = ctk.CTkFrame(card, fg_color="transparent")
        frm_actions.pack(fill="x", padx=16, pady=4)

        btn_make_pdf = ctk.CTkButton(
            frm_actions,
            text="📝 สร้างและบันทึกรายงาน PDF ทันที",
            command=self._export_pdf_direct,
            font=ctk.CTkFont(family=self.font_fam, size=12, weight="bold"),
            fg_color="#38A169",
            hover_color="#276749",
            height=36
        )
        btn_make_pdf.pack(side="left", padx=(0, 10))

        btn_open_folder = ctk.CTkButton(
            frm_actions,
            text="📂 เปิดโฟลเดอร์รายงาน (Open Reports)",
            command=self._open_reports_folder,
            font=ctk.CTkFont(family=self.font_fam, size=12),
            fg_color="#4A5568",
            height=36
        )
        btn_open_folder.pack(side="left")

        # Report Preview Box
        self.txt_pdf_log = ctk.CTkTextbox(tab, height=340, font=ctk.CTkFont(family="Consolas", size=11), corner_radius=6)
        self.txt_pdf_log.pack(fill="both", expand=True, padx=4, pady=(8, 8))
        self.txt_pdf_log.insert("end", "[INFO] คลิก 'สร้างและบันทึกรายงาน PDF ทันที' เพื่อออกรายงานฉบับล่าสุด\n")

    # --- TAB 6: SETTINGS & VAULT ---
    def _init_settings_tab(self):
        tab = ctk.CTkScrollableFrame(self.view_container, fg_color="transparent")
        self.tabs["settings"] = tab

        # Server Profile Editor Card
        card_srv = ctk.CTkFrame(tab, corner_radius=8)
        card_srv.pack(fill="x", pady=(0, 10), padx=4, ipady=8)

        ctk.CTkLabel(
            card_srv,
            text="⚙️ กำหนดค่าเซิร์ฟเวอร์ & คลังข้อมูลเข้ารหัส (Secure Vault)",
            font=ctk.CTkFont(family=self.font_fam, size=15, weight="bold")
        ).pack(anchor="w", padx=14, pady=(6, 2))

        ctk.CTkLabel(
            card_srv,
            text="รหัสผ่านทั้งหมดจะถูกเข้ารหัสสองชั้น (AES-256-GCM + zlib Level 9 Vault) ปลอดภัย 100%",
            font=ctk.CTkFont(family=self.font_fam, size=11),
            text_color="gray"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # Form Inputs Grid
        frm_form = ctk.CTkFrame(card_srv, fg_color="transparent")
        frm_form.pack(fill="x", padx=14, pady=4)

        # Row 1: Name & Host
        ctk.CTkLabel(frm_form, text="ชื่อเซิร์ฟเวอร์ (Name):", font=ctk.CTkFont(family=self.font_fam, size=12)).grid(row=0, column=0, sticky="w", pady=4)
        self.entry_srv_name = ctk.CTkEntry(frm_form, width=280)
        self.entry_srv_name.grid(row=0, column=1, sticky="w", padx=8, pady=4)

        ctk.CTkLabel(frm_form, text="Host / IP Address:", font=ctk.CTkFont(family=self.font_fam, size=12)).grid(row=0, column=2, sticky="w", padx=(16, 0), pady=4)
        self.entry_srv_host = ctk.CTkEntry(frm_form, width=220)
        self.entry_srv_host.grid(row=0, column=3, sticky="w", padx=8, pady=4)

        # Row 2: SSH Port & User
        ctk.CTkLabel(frm_form, text="SSH Port (ค่าเริ่มต้น 22):", font=ctk.CTkFont(family=self.font_fam, size=12)).grid(row=1, column=0, sticky="w", pady=4)
        self.entry_ssh_port = ctk.CTkEntry(frm_form, width=100)
        self.entry_ssh_port.insert(0, "22")
        self.entry_ssh_port.grid(row=1, column=1, sticky="w", padx=8, pady=4)

        ctk.CTkLabel(frm_form, text="SSH User (เช่น root):", font=ctk.CTkFont(family=self.font_fam, size=12)).grid(row=1, column=2, sticky="w", padx=(16, 0), pady=4)
        self.entry_ssh_user = ctk.CTkEntry(frm_form, width=220)
        self.entry_ssh_user.insert(0, "root")
        self.entry_ssh_user.grid(row=1, column=3, sticky="w", padx=8, pady=4)

        # Row 3: SSH Password (Masked with Eye Toggle)
        ctk.CTkLabel(frm_form, text="SSH Password:", font=ctk.CTkFont(family=self.font_fam, size=12)).grid(row=2, column=0, sticky="w", pady=4)
        frm_ssh_pw = ctk.CTkFrame(frm_form, fg_color="transparent")
        frm_ssh_pw.grid(row=2, column=1, sticky="w", padx=8, pady=4)

        self.entry_ssh_pass = ctk.CTkEntry(frm_ssh_pw, width=230, show="*")
        self.entry_ssh_pass.pack(side="left")
        self.btn_eye_ssh = ctk.CTkButton(
            frm_ssh_pw, text="👁️", width=36,
            command=lambda: self._toggle_eye(self.entry_ssh_pass, self.btn_eye_ssh)
        )
        self.btn_eye_ssh.pack(side="left", padx=(4, 0))

        # Row 4: MySQL Port & User
        ctk.CTkLabel(frm_form, text="MySQL Port (3306):", font=ctk.CTkFont(family=self.font_fam, size=12)).grid(row=3, column=0, sticky="w", pady=4)
        self.entry_my_port = ctk.CTkEntry(frm_form, width=100)
        self.entry_my_port.insert(0, "3306")
        self.entry_my_port.grid(row=3, column=1, sticky="w", padx=8, pady=4)

        ctk.CTkLabel(frm_form, text="MySQL User:", font=ctk.CTkFont(family=self.font_fam, size=12)).grid(row=3, column=2, sticky="w", padx=(16, 0), pady=4)
        self.entry_my_user = ctk.CTkEntry(frm_form, width=220)
        self.entry_my_user.insert(0, "root")
        self.entry_my_user.grid(row=3, column=3, sticky="w", padx=8, pady=4)

        # Row 5: MySQL Password (Masked)
        ctk.CTkLabel(frm_form, text="MySQL Password:", font=ctk.CTkFont(family=self.font_fam, size=12)).grid(row=4, column=0, sticky="w", pady=4)
        frm_my_pw = ctk.CTkFrame(frm_form, fg_color="transparent")
        frm_my_pw.grid(row=4, column=1, sticky="w", padx=8, pady=4)

        self.entry_my_pass = ctk.CTkEntry(frm_my_pw, width=230, show="*")
        self.entry_my_pass.pack(side="left")
        self.btn_eye_my = ctk.CTkButton(
            frm_my_pw, text="👁️", width=36,
            command=lambda: self._toggle_eye(self.entry_my_pass, self.btn_eye_my)
        )
        self.btn_eye_my.pack(side="left", padx=(4, 0))

        # Buttons
        frm_btn_srv = ctk.CTkFrame(card_srv, fg_color="transparent")
        frm_btn_srv.pack(fill="x", padx=14, pady=(12, 6))

        btn_save = ctk.CTkButton(
            frm_btn_srv,
            text="💾 บันทึกลง Vault ที่เข้ารหัส",
            command=self._save_current_server_form,
            font=ctk.CTkFont(family=self.font_fam, size=12, weight="bold"),
            fg_color="#2B6CB0",
            width=200
        )
        btn_save.pack(side="left", padx=(0, 10))

        btn_new = ctk.CTkButton(
            frm_btn_srv,
            text="➕ เพิ่มเซิร์ฟเวอร์ใหม่",
            command=self._clear_server_form,
            font=ctk.CTkFont(family=self.font_fam, size=12),
            width=140
        )
        btn_new.pack(side="left", padx=(0, 10))

        btn_del = ctk.CTkButton(
            frm_btn_srv,
            text="🗑️ ลบเซิร์ฟเวอร์นี้",
            command=self._delete_current_server,
            font=ctk.CTkFont(family=self.font_fam, size=12),
            fg_color="#E53E3E",
            hover_color="#C53030",
            width=130
        )
        btn_del.pack(side="left")

        # Update Testing & Simulation Card
        card_upd = ctk.CTkFrame(tab, corner_radius=8)
        card_upd.pack(fill="x", pady=(10, 10), padx=4, ipady=8)

        ctk.CTkLabel(
            card_upd,
            text="🔄 ระบบตรวจสอบและจำลองการอัปเดต (Auto-Update Engine)",
            font=ctk.CTkFont(family=self.font_fam, size=15, weight="bold")
        ).pack(anchor="w", padx=14, pady=(6, 2))

        ctk.CTkLabel(
            card_upd,
            text="สถาปัตยกรรม External PowerShell Zero-Lock Swap สลับไฟล์ EXE อัตโนมัติโดยไม่ติด File Lock",
            font=ctk.CTkFont(family=self.font_fam, size=11),
            text_color="gray"
        ).pack(anchor="w", padx=14, pady=(0, 8))

        frm_upd_row = ctk.CTkFrame(card_upd, fg_color="transparent")
        frm_upd_row.pack(fill="x", padx=14, pady=4)

        btn_chk_now = ctk.CTkButton(
            frm_upd_row,
            text="🔍 ตรวจสอบอัปเดตจากเซิร์ฟเวอร์",
            command=self._check_updates_async,
            font=ctk.CTkFont(family=self.font_fam, size=12),
            fg_color="#2B6CB0",
            width=210
        )
        btn_chk_now.pack(side="left", padx=(0, 10))

        btn_sim_swap = ctk.CTkButton(
            frm_upd_row,
            text="🧪 ทดสอบสลับไฟล์อัปเดต (Simulate Swap)",
            command=self._simulate_update_swap,
            font=ctk.CTkFont(family=self.font_fam, size=12),
            fg_color="#D69E2E",
            hover_color="#B7791F",
            width=220
        )
        btn_sim_swap.pack(side="left")

    def _toggle_eye(self, entry_widget: ctk.CTkEntry, btn_widget: ctk.CTkButton):
        if entry_widget.cget("show") == "*":
            entry_widget.configure(show="")
            btn_widget.configure(text="🙈")
        else:
            entry_widget.configure(show="*")
            btn_widget.configure(text="👁️")

    # --- TAB NAVIGATION ---
    def _switch_tab(self, active_id: str):
        for tab_id, tab_widget in self.tabs.items():
            if tab_id == active_id:
                tab_widget.pack(fill="both", expand=True)
                if tab_id in self.nav_btns:
                    self.nav_btns[tab_id].configure(fg_color=("gray75", "gray25"))
            else:
                tab_widget.pack_forget()
                if tab_id in self.nav_btns:
                    self.nav_btns[tab_id].configure(fg_color="transparent")

    def _show_tab_dashboard(self): self._switch_tab("dashboard")
    def _show_tab_network(self): self._switch_tab("network")
    def _show_tab_linux(self): self._switch_tab("linux")
    def _show_tab_mysql(self): self._switch_tab("mysql")
    def _show_tab_pdf(self): self._switch_tab("pdf")
    def _show_tab_settings(self): self._switch_tab("settings")

    def _change_theme(self, new_mode: str):
        ctk.set_appearance_mode(new_mode)
        self.config_mgr.set_setting("theme", new_mode)

    # --- LICENSE & UPDATE HANDLING ---
    def _open_license_dialog(self):
        LicenseDialog(self, self.license_mgr, self.config_mgr, on_activated_callback=self._refresh_license_badge)

    def _refresh_license_badge(self):
        key = self.config_mgr.get_setting("license_key", "")
        if key:
            is_valid, msg, _ = self.license_mgr.verify_license_key(key)
            if is_valid:
                self.lbl_trial.configure(text="🛡️ สิทธิ์: Activated (ตลอดชีพ)", text_color="#38A169")
                return

        trial = self.license_mgr.get_trial_status()
        if trial["is_expired"]:
            self.lbl_trial.configure(text="⚠️ สิทธิ์ทดลองใช้งานหมดอายุ", text_color="#E53E3E")
        else:
            self.lbl_trial.configure(text=f"⏳ ทดลองใช้เหลือ {trial['days_left']} วัน", text_color="#38A169")

    def _check_updates_async(self):
        self.status_var.set("กำลังตรวจสอบการอัปเดตเวอร์ชันใหม่...")

        def _work():
            has_update, manifest, msg = self.updater.check_for_updates()
            if has_update and manifest:
                latest_ver = manifest.get("latest_version") or manifest.get("version", "vNew")
                notes = manifest.get("release_notes") or manifest.get("notes", "มีการปรับปรุงประสิทธิภาพและความปลอดภัย")
                download_url = manifest.get("download_url", "")
                self.after(0, lambda: self.status_var.set(f"พบเวอร์ชันใหม่ v{latest_ver}"))

                def _prompt_update():
                    if messagebox.askyesno(
                        "พบการอัปเดตใหม่",
                        f"🎉 พบเวอร์ชันใหม่: v{latest_ver}\nเวอร์ชันปัจจุบัน: v{APP_VERSION}\n\nรายละเอียดการอัปเดต:\n{notes}\n\nต้องการดาวน์โหลดและติดตั้งอัปเดตทันทีหรือไม่?\n(โปรแกรมจะปิดตัวลงเพื่อคืน File Lock และสลับไฟล์ EXE ตัวใหม่อัตโนมัติ)"
                    ):
                        if download_url:
                            self.updater.download_and_apply_update(download_url, latest_ver)
                        else:
                            messagebox.showwarning("คำเตือน", "ไม่พบ Download URL ในข้อมูล Manifest")
                self.after(0, _prompt_update)
            else:
                self.after(0, lambda: self.status_var.set(f"คุณกำลังใช้งานเวอร์ชันล่าสุด (v{APP_VERSION})"))
                self.after(0, lambda: messagebox.showinfo(
                    "ตรวจสอบอัปเดต",
                    f"{msg}\nเวอร์ชันปัจจุบัน: v{APP_VERSION}"
                ))

        self.executor.submit(_work)

    def _simulate_update_swap(self):
        """Allows user to test the PowerShell file swap mechanism directly."""
        file_path = filedialog.askopenfilename(
            title="เลือกไฟล์ .EXE เพื่อทดสอบการสลับไฟล์อัปเดต",
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        if messagebox.askyesno(
            "ยืนยันการทดสอบอัปเดต",
            f"ระบบจะจำลองการสลับไฟล์โดยนำ:\n{file_path}\n\nมาแทนที่โปรแกรมที่กำลังทำงานอยู่ และเปิดโปรแกรมขึ้นมาใหม่โดยอัตโนมัติ\n\nต้องการเริ่มการทดสอบทันทีหรือไม่?"
        ):
            self.updater.download_and_apply_update(file_path, "TEST_SIMULATION")

    # --- SERVER DATA MANAGEMENT ---
    def _load_servers_into_ui(self):
        servers = self.config_mgr.get_servers()
        if not servers:
            self.server_menu.configure(values=["(ยังไม่มีเซิร์ฟเวอร์)"])
            return

        names = [f"{s.get('name', 'Server')} ({s.get('host', '')})" for s in servers]
        self.server_menu.configure(values=names)
        self.current_server_id.set(names[0])
        self._populate_server_form(servers[0])

    def _get_selected_server(self) -> Optional[Dict[str, Any]]:
        current = self.current_server_id.get()
        servers = self.config_mgr.get_servers()
        for s in servers:
            opt = f"{s.get('name', 'Server')} ({s.get('host', '')})"
            if opt == current:
                return s
        return servers[0] if servers else None

    def _on_server_selected(self, choice: str):
        servers = self.config_mgr.get_servers()
        for s in servers:
            opt = f"{s.get('name', 'Server')} ({s.get('host', '')})"
            if opt == choice:
                self._populate_server_form(s)
                break

    def _populate_server_form(self, srv: Dict[str, Any]):
        self.entry_srv_name.delete(0, "end")
        self.entry_srv_name.insert(0, srv.get("name", ""))

        self.entry_srv_host.delete(0, "end")
        self.entry_srv_host.insert(0, srv.get("host", ""))
        self.entry_net_host.delete(0, "end")
        self.entry_net_host.insert(0, srv.get("host", ""))

        self.entry_ssh_port.delete(0, "end")
        self.entry_ssh_port.insert(0, str(srv.get("ssh_port", 22)))

        self.entry_ssh_user.delete(0, "end")
        self.entry_ssh_user.insert(0, srv.get("ssh_user", "root"))

        self.entry_ssh_pass.delete(0, "end")
        self.entry_ssh_pass.insert(0, srv.get("ssh_password", ""))

        self.entry_my_port.delete(0, "end")
        self.entry_my_port.insert(0, str(srv.get("mysql_port", 3306)))

        self.entry_my_user.delete(0, "end")
        self.entry_my_user.insert(0, srv.get("mysql_user", "root"))

        self.entry_my_pass.delete(0, "end")
        self.entry_my_pass.insert(0, srv.get("mysql_password", ""))

    def _clear_server_form(self):
        self.entry_srv_name.delete(0, "end")
        self.entry_srv_name.insert(0, "New Linux Server")
        self.entry_srv_host.delete(0, "end")
        self.entry_srv_host.insert(0, "192.168.1.100")
        self.entry_ssh_port.delete(0, "end")
        self.entry_ssh_port.insert(0, "22")
        self.entry_ssh_user.delete(0, "end")
        self.entry_ssh_user.insert(0, "root")
        self.entry_ssh_pass.delete(0, "end")
        self.entry_my_port.delete(0, "end")
        self.entry_my_port.insert(0, "3306")
        self.entry_my_user.delete(0, "end")
        self.entry_my_user.insert(0, "root")
        self.entry_my_pass.delete(0, "end")
        messagebox.showinfo("เพิ่มเซิร์ฟเวอร์", "กรอกข้อมูลและกด 'บันทึกลง Vault ที่เข้ารหัส' เพื่อจัดเก็บ")

    def _save_current_server_form(self):
        host = self.entry_srv_host.get().strip()
        name = self.entry_srv_name.get().strip() or host
        if not host:
            messagebox.showwarning("คำเตือน", "กรุณาระบุ Host / IP Address")
            return

        srv_obj = {
            "id": f"srv_{host.replace('.', '_')}",
            "name": name,
            "host": host,
            "ssh_port": int(self.entry_ssh_port.get().strip() or "22"),
            "ssh_user": self.entry_ssh_user.get().strip() or "root",
            "ssh_password": self.entry_ssh_pass.get(),
            "mysql_port": int(self.entry_my_port.get().strip() or "3306"),
            "mysql_user": self.entry_my_user.get().strip() or "root",
            "mysql_password": self.entry_my_pass.get(),
            "mysql_db": "mysql"
        }

        self.config_mgr.add_or_update_server(srv_obj)
        self._load_servers_into_ui()
        messagebox.showinfo("สำเร็จ", f"บันทึกเซิร์ฟเวอร์ '{name}' ลงใน Config Vault สำเร็จเรียบร้อย!")

    def _delete_current_server(self):
        srv = self._get_selected_server()
        if not srv:
            return
        if messagebox.askyesno("ยืนยันการลบ", f"ต้องการลบเซิร์ฟเวอร์ '{srv.get('name')}' ออกจากระบบหรือไม่?"):
            self.config_mgr.delete_server(srv.get("id"))
            self._load_servers_into_ui()

    # --- ASYNC EXECUTIONS ---
    def _append_log(self, textbox: ctk.CTkTextbox, text: str):
        self.after(0, lambda: self._do_append(textbox, text))

    def _do_append(self, textbox: ctk.CTkTextbox, text: str):
        textbox.insert("end", text)
        textbox.see("end")

    def _run_ping_async(self):
        host = self.entry_net_host.get().strip()
        if not host:
            return
        self.status_var.set(f"กำลัง Ping {host}...")
        self.txt_net_log.insert("end", f"\n[PING] กำลังทดสอบส่งสัญญาณไปยัง {host}...\n")

        def _work():
            res = NetworkDiagnostics.ping(host)
            self._append_log(self.txt_net_log, res["raw_output"] + f"\n[สรุปผล] สถานะ: {res['status_text']}\n")
            self.after(0, lambda: self.status_var.set("Ping เสร็จสิ้น"))
            color = "#38A169" if res["success"] and res["avg_ms"] <= 50 else "#D69E2E" if res["success"] else "#E53E3E"
            self.after(0, lambda: self.card_ping.value_label.configure(
                text=f"{res['avg_ms']} ms ({res['packet_loss_pct']}% loss)", text_color=color
            ))
            self.audit_cache["net_ping"] = res

        self.executor.submit(_work)

    def _run_tracert_async(self):
        host = self.entry_net_host.get().strip()
        if not host:
            return
        self.status_var.set(f"กำลังรัน Traceroute ไปยัง {host}...")
        self.txt_net_log.insert("end", f"\n[TRACEROUTE] เริ่มค้นหาเส้นทาง Hop ไปยัง {host}...\n")

        def _on_hop(h):
            self._append_log(self.txt_net_log, f"Hop {h['hop']}: {h['rtt_info']} -> {h['ip']}\n")

        def _work():
            hops = NetworkDiagnostics.traceroute(host, hop_callback=_on_hop)
            self._append_log(self.txt_net_log, f"[TRACEROUTE] สำรวจครบ {len(hops)} Hops เรียบร้อย\n")
            self.after(0, lambda: self.status_var.set("Traceroute เสร็จสิ้น"))
            self.audit_cache["net_tracert"] = hops

        self.executor.submit(_work)

    def _run_port_scan_async(self):
        host = self.entry_net_host.get().strip()
        if not host:
            return
        self.status_var.set(f"กำลังสแกนพอร์ต {host}...")
        self.txt_net_log.insert("end", f"\n[PORT SCAN] เริ่มสแกนพอร์ตมาตรฐาน 14 พอร์ตบน {host}...\n")

        def _work():
            ports = NetworkDiagnostics.scan_ports(host)
            for p in ports:
                status_icon = "🟢 OPEN" if p["status"] == "OPEN" else "⚪ CLOSED"
                self._append_log(self.txt_net_log, f"Port {p['port']:<5} ({p['service']:<10}): {status_icon} [{p['risk']}]\n")
            self.audit_cache["port_scan"] = ports
            self.after(0, lambda: self.status_var.set("สแกนพอร์ตเสร็จสิ้น"))

        self.executor.submit(_work)

    def _run_linux_audit_async(self):
        srv = self._get_selected_server()
        if not srv:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกเซิร์ฟเวอร์ก่อน")
            return

        self.status_var.set(f"กำลังเชื่อมต่อ SSH ตรวจสอบ {srv.get('host')}...")
        self.txt_linux_log.insert("end", f"\n[LINUX SSH] เชื่อมต่อไปยัง {srv.get('host')}:{srv.get('ssh_port')} ผู้ใช้ {srv.get('ssh_user')}...\n")

        def _work():
            auditor = LinuxSSHAuditor(
                host=srv.get("host"),
                port=srv.get("ssh_port", 22),
                user=srv.get("ssh_user", "root"),
                password=srv.get("ssh_password", "")
            )
            res = auditor.run_full_audit()
            self.audit_cache["linux_audit"] = res

            if not res.get("success"):
                self._append_log(self.txt_linux_log, f"❌ การเชื่อมต่อล้มเหลว: {res.get('error')}\n")
                self.after(0, lambda: self.status_var.set("SSH Connection Error"))
                return

            os_i = res.get("os_info", {})
            res_m = res.get("resources", {})
            fw = res.get("firewall", {})
            pt = res.get("patches", {})
            up = res.get("uptime_load", {})

            # Format Terminal Output
            out_text = f"""
================================================================================
  [ผลการตรวจสอบ LINUX SERVER: {srv.get('name')} ({srv.get('host')})]
================================================================================
• ระบบปฏิบัติการ: {os_i.get('distro')} (Kernel: {os_i.get('kernel')})
• สถาปัตยกรรม: {os_i.get('arch')} | Hostname: {os_i.get('hostname')}
• CPU Cores: {res_m.get('cpu_cores')} | RAM: {res_m.get('ram_used_mb')}/{res_m.get('ram_total_mb')} MB ({res_m.get('ram_pct')}%)
• Uptime & Load: {up.get('raw_uptime')}
• สถานะ Firewall: {fw.get('status_detail')} ({fw.get('type')})
• การอัปเดตแพตช์: {pt.get('status_text')}
• คะแนนความปลอดภัย: {res.get('security_score')}/100 (เกรด {res.get('security_grade')})

[รายการพาร์ติชันฮาร์ดดิสก์]:
"""
            for d in res.get("disks", []):
                out_text += f"  - {d.get('mount'):<15} {d.get('filesystem'):<20} {d.get('used')}/{d.get('size')} ({d.get('use_pct')}%) {'⚠️ WARNING' if d.get('is_warning') else '✅ OK'}\n"

            out_text += "\n[สถานะเซอร์วิสสำคัญ]:\n"
            for s in res.get("services", []):
                icon = "🟢 ACTIVE" if s.get("is_running") else "⚪ INACTIVE"
                out_text += f"  - {s.get('service'):<28}: {icon}\n"

            out_text += "================================================================================\n"
            self._append_log(self.txt_linux_log, out_text)

            # Update Dashboard & Linux Tab Structured Cards
            self.after(0, lambda: self.card_os.value_label.configure(
                text=f"{os_i.get('distro', 'Linux')[:18]}...", text_color="#38A169"
            ))
            self.after(0, lambda: self.card_l_os.value_label.configure(
                text=f"{os_i.get('distro', 'Linux')[:16]}...", text_color="#38A169"
            ))

            self.after(0, lambda: self.card_l_cpu.value_label.configure(
                text=f"{res_m.get('cpu_cores')} Cores (Load: {up.get('load_1m', 0.0)})", text_color="#38A169"
            ))

            ram_color = "#E53E3E" if res_m.get("ram_pct", 0) > 85 else "#38A169"
            self.after(0, lambda: self.card_l_ram.value_label.configure(
                text=f"{res_m.get('ram_pct')}% ({res_m.get('ram_used_mb')} MB)", text_color=ram_color
            ))

            fw_color = "#38A169" if fw.get("is_active") else "#E53E3E"
            fw_text = f"FW: {'ON' if fw.get('is_active') else 'OFF'} | Patches: {pt.get('total_upgrades', 0)}"
            self.after(0, lambda: self.card_fw.value_label.configure(
                text="ACTIVE" if fw.get("is_active") else "DISABLED", text_color=fw_color
            ))
            self.after(0, lambda: self.card_l_fw.value_label.configure(
                text=fw_text, text_color=fw_color
            ))

            self.after(0, lambda: self.status_var.set("Linux Audit เสร็จสิ้น"))

        self.executor.submit(_work)

    def _run_preset_command(self, cmd: str, desc: str):
        """1-Click quick command runner."""
        srv = self._get_selected_server()
        if not srv:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกเซิร์ฟเวอร์ก่อน")
            return

        self.entry_linux_cmd.delete(0, "end")
        self.entry_linux_cmd.insert(0, cmd)
        self.txt_linux_log.insert("end", f"\n[1-CLICK COMMAND] {desc}\n$ {cmd}\n")
        self.status_var.set(f"กำลังรัน: {desc}...")

        def _work():
            auditor = LinuxSSHAuditor(
                host=srv.get("host"),
                port=srv.get("ssh_port", 22),
                user=srv.get("ssh_user", "root"),
                password=srv.get("ssh_password", "")
            )
            _, out, err = auditor.exec_command(cmd)
            auditor.close()
            resp = out if out else err
            self._append_log(self.txt_linux_log, resp + "\n")
            self.after(0, lambda: self.status_var.set(f"คำสั่ง '{desc}' สำเร็จ"))

        self.executor.submit(_work)

    def _exec_custom_linux_cmd_async(self):
        srv = self._get_selected_server()
        cmd = self.entry_linux_cmd.get().strip()
        if not srv or not cmd:
            return

        self.txt_linux_log.insert("end", f"\n$ {cmd}\n")
        self.status_var.set(f"กำลังรัน: {cmd}")

        def _work():
            auditor = LinuxSSHAuditor(
                host=srv.get("host"),
                port=srv.get("ssh_port", 22),
                user=srv.get("ssh_user", "root"),
                password=srv.get("ssh_password", "")
            )
            _, out, err = auditor.exec_command(cmd)
            auditor.close()
            resp = out if out else err
            self._append_log(self.txt_linux_log, resp + "\n")
            self.after(0, lambda: self.status_var.set("คำสั่งสำเร็จ"))

        self.executor.submit(_work)

    def _run_mysql_test_async(self):
        srv = self._get_selected_server()
        if not srv:
            return

        self.status_var.set(f"กำลังทดสอบ MySQL {srv.get('host')}...")
        self.txt_mysql_log.insert("end", f"\n[MYSQL] ทดสอบเชื่อมต่อ {srv.get('host')}:{srv.get('mysql_port')} ผู้ใช้ {srv.get('mysql_user')}...\n")

        def _work():
            auditor = MySQLAuditor(
                host=srv.get("host"),
                port=srv.get("mysql_port", 3306),
                user=srv.get("mysql_user", "root"),
                password=srv.get("mysql_password", "")
            )
            is_ok, msg = auditor.test_connection()
            icon = "✅" if is_ok else "❌"
            self._append_log(self.txt_mysql_log, f"{icon} {msg}\n")
            self.after(0, lambda: self.status_var.set("ทดสอบ MySQL เสร็จสิ้น"))

        self.executor.submit(_work)

    def _run_mysql_audit_async(self):
        srv = self._get_selected_server()
        if not srv:
            return

        self.status_var.set(f"กำลังดึงข้อมูลฐานข้อมูล MySQL {srv.get('host')}...")
        self.txt_mysql_log.insert("end", f"\n[MYSQL AUDIT] เริ่มตรวจสอบขนาดฐานข้อมูลและประเมินสิทธิ์ความปลอดภัย...\n")

        def _work():
            auditor = MySQLAuditor(
                host=srv.get("host"),
                port=srv.get("mysql_port", 3306),
                user=srv.get("mysql_user", "root"),
                password=srv.get("mysql_password", "")
            )
            res = auditor.run_full_db_audit()
            self.audit_cache["mysql_audit"] = res

            if not res.get("success"):
                self._append_log(self.txt_mysql_log, f"❌ ข้อผิดพลาด: {res.get('error')}\n")
                self.after(0, lambda: self.status_var.set("MySQL Error"))
                return

            out_text = f"""
================================================================================
  [ผลการตรวจสอบ MYSQL DATABASE]
================================================================================
• MySQL Version: {res.get('version')}
• Uptime: {res.get('uptime_seconds') // 3600} ชั่วโมง
• Threads Connected: {res.get('threads_connected')} / {res.get('max_connections')}
• Buffer Pool Size: {res.get('buffer_pool_mb')} MB
• คะแนนความปลอดภัยฐานข้อมูล: {res.get('db_score')}/100

[รายการฐานข้อมูลและขนาดพื้นที่]:
"""
            for s in res.get("schemas", [])[:12]:
                out_text += f"  - {s.get('schema_name'):<25}: {float(s.get('size_mb', 0)):>8.2f} MB ({s.get('table_count')} tables)\n"

            out_text += "\n[รายการตรวจสอบความปลอดภัย]:\n"
            for c in res.get("security_checks", []):
                out_text += f"  - [{c.get('status')}]: {c.get('desc')}\n"

            out_text += "================================================================================\n"
            self._append_log(self.txt_mysql_log, out_text)

            # Update MySQL Cards
            self.after(0, lambda: self.card_my_ver.value_label.configure(
                text=res.get("version", "MySQL")[:18], text_color="#38A169"
            ))
            self.after(0, lambda: self.card_my_up.value_label.configure(
                text=f"{res.get('uptime_seconds') // 3600} ชั่วโมง", text_color="#38A169"
            ))
            self.after(0, lambda: self.card_my_bp.value_label.configure(
                text=f"{res.get('buffer_pool_mb')} MB", text_color="#38A169"
            ))
            self.after(0, lambda: self.card_my_conn.value_label.configure(
                text=f"{res.get('threads_connected')} / {res.get('max_connections')}", text_color="#38A169"
            ))

            self.after(0, lambda: self.card_db.value_label.configure(
                text=f"{res.get('version')[:15]} ({res.get('threads_connected')} conn)", text_color="#38A169"
            ))
            self.after(0, lambda: self.status_var.set("MySQL Audit เสร็จสิ้น"))

        self.executor.submit(_work)

    def _run_full_audit_async(self):
        srv = self._get_selected_server()
        if not srv:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกเซิร์ฟเวอร์ก่อน")
            return

        self.status_var.set(f"กำลังรันการตรวจสอบแบบละเอียดครบวงจร...")
        self.txt_dash_log.insert("end", f"\n>>> [เริ่มการตรวจสอบระบบเต็มรูปแบบ: {srv.get('name')} ({srv.get('host')})] <<<\n")

        def _work():
            # 1. Ping
            self._append_log(self.txt_dash_log, "-> 1. ทดสอบ Network Ping...\n")
            ping_res = NetworkDiagnostics.ping(srv.get("host"))
            self.audit_cache["net_ping"] = ping_res

            # 2. Ports
            self._append_log(self.txt_dash_log, "-> 2. สแกนพอร์ตมาตรฐาน...\n")
            port_res = NetworkDiagnostics.scan_ports(srv.get("host"))
            self.audit_cache["port_scan"] = port_res

            # 3. Linux SSH
            self._append_log(self.txt_dash_log, "-> 3. เชื่อมต่อ SSH ตรวจสอบ Linux OS, Firewall & Patch...\n")
            ssh_aud = LinuxSSHAuditor(
                host=srv.get("host"),
                port=srv.get("ssh_port", 22),
                user=srv.get("ssh_user", "root"),
                password=srv.get("ssh_password", "")
            )
            linux_res = ssh_aud.run_full_audit()
            self.audit_cache["linux_audit"] = linux_res

            # 4. MySQL
            self._append_log(self.txt_dash_log, "-> 4. เชื่อมต่อตรวจสอบ MySQL Database...\n")
            db_aud = MySQLAuditor(
                host=srv.get("host"),
                port=srv.get("mysql_port", 3306),
                user=srv.get("mysql_user", "root"),
                password=srv.get("mysql_password", "")
            )
            db_res = db_aud.run_full_db_audit()
            self.audit_cache["mysql_audit"] = db_res

            # Update GUI Cards
            score = linux_res.get("security_score", 100) if linux_res.get("success") else 0
            self._append_log(self.txt_dash_log, f"\n✅ การตรวจสอบเสร็จสมบูรณ์! คะแนนความปลอดภัยรวม: {score}/100\n")
            self.after(0, lambda: self.status_var.set(f"Full Audit เสร็จสมบูรณ์ (Score: {score}/100)"))

        self.executor.submit(_work)

    def _export_pdf_direct(self):
        srv = self._get_selected_server()
        if not srv:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกเซิร์ฟเวอร์ก่อน")
            return

        self.status_var.set("กำลังสร้างไฟล์ PDF รายงานการประเมิน...")

        def _work():
            net_res = self.audit_cache.get("net_ping")
            if not net_res:
                net_res = NetworkDiagnostics.ping(srv.get("host"))
                self.audit_cache["net_ping"] = net_res

            linux_res = self.audit_cache.get("linux_audit")
            if not linux_res:
                ssh_aud = LinuxSSHAuditor(
                    host=srv.get("host"),
                    port=srv.get("ssh_port", 22),
                    user=srv.get("ssh_user", "root"),
                    password=srv.get("ssh_password", "")
                )
                linux_res = ssh_aud.run_full_audit()
                self.audit_cache["linux_audit"] = linux_res

            db_res = self.audit_cache.get("mysql_audit")
            port_res = self.audit_cache.get("port_scan")

            pdf_path = self.pdf_generator.generate_audit_report(
                server_name=srv.get("name", "Server"),
                host=srv.get("host"),
                linux_audit=linux_res,
                mysql_audit=db_res,
                net_audit=net_res,
                port_audit=port_res
            )

            msg = f"สร้างรายงาน PDF สำเร็จเรียบร้อย:\n{pdf_path}"
            self._append_log(self.txt_pdf_log, f"\n[SUCCESS] {msg}\n")
            self.after(0, lambda: self.status_var.set("สร้าง PDF สำเร็จ"))
            self.after(0, lambda: messagebox.showinfo("ออกรายงานสำเร็จ", msg))

            try:
                if sys.platform == "win32":
                    os.startfile(pdf_path)
            except Exception:
                pass

        self.executor.submit(_work)

    def _open_reports_folder(self):
        out_dir = os.path.abspath("reports")
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(out_dir)
        else:
            subprocess.Popen(["xdg-open", out_dir])


if __name__ == "__main__":
    app = ServerAdminApp()
    app.mainloop()
