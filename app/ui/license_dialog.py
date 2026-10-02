# -*- coding: utf-8 -*-
"""
License Key Activation Dialog.
Displays Hardware ID (HWID), masked License Key entry with eye toggle,
and handles activation with HMAC-SHA256 signature verification.
"""

import sys
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from app.core.security import get_machine_hwid
from app.core.font_manager import FontManager


class LicenseDialog(ctk.CTkToplevel):
    """Modal dialog for License Key registration and status check."""

    def __init__(self, parent, license_mgr, config_mgr, on_activated_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.license_mgr = license_mgr
        self.config_mgr = config_mgr
        self.on_activated_callback = on_activated_callback
        self.font_fam = FontManager.resolve_best_font()

        self.title("เปิดใช้งาน License Key - Soft4U Server Admin Suite")
        self.geometry("640x520")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self._center_window(640, 520)
        self._build_ui()
        self.grab_set()

    def _center_window(self, width: int, height: int):
        self.update_idletasks()
        pw = self.parent.winfo_width()
        ph = self.parent.winfo_height()
        px = self.parent.winfo_x()
        py = self.parent.winfo_y()
        x = px + (pw - width) // 2
        y = py + (ph - height) // 2
        self.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")

    def _build_ui(self):
        # Header Box
        frm_hdr = ctk.CTkFrame(self, corner_radius=10, fg_color=("#E2E8F0", "#1A202C"))
        frm_hdr.pack(fill="x", padx=20, pady=(20, 12), ipady=8)

        ctk.CTkLabel(
            frm_hdr,
            text="🔑 ลงทะเบียนเปิดใช้งานลิขสิทธิ์ (License Activation)",
            font=ctk.CTkFont(family=self.font_fam, size=16, weight="bold")
        ).pack(anchor="w", padx=16, pady=(4, 2))

        ctk.CTkLabel(
            frm_hdr,
            text="ผูกกับรหัสประจำเครื่องคอมพิวเตอร์ (Hardware ID) ปลอดภัยตามมาตรฐาน Soft4UApp Enterprise",
            font=ctk.CTkFont(family=self.font_fam, size=11),
            text_color="gray"
        ).pack(anchor="w", padx=16, pady=(0, 4))

        # HWID Card
        frm_hwid = ctk.CTkFrame(self, corner_radius=8)
        frm_hwid.pack(fill="x", padx=20, pady=8, ipady=4)

        ctk.CTkLabel(
            frm_hwid,
            text="รหัสประจำเครื่องนี้ (Machine HWID):",
            font=ctk.CTkFont(family=self.font_fam, size=12, weight="bold"),
            text_color="gray"
        ).pack(anchor="w", padx=14, pady=(8, 2))

        frm_hwid_row = ctk.CTkFrame(frm_hwid, fg_color="transparent")
        frm_hwid_row.pack(fill="x", padx=14, pady=(0, 8))

        self.hwid_str = get_machine_hwid()
        self.entry_hwid = ctk.CTkEntry(
            frm_hwid_row,
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color=("gray90", "gray20")
        )
        self.entry_hwid.insert(0, self.hwid_str)
        self.entry_hwid.configure(state="readonly")
        self.entry_hwid.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_copy = ctk.CTkButton(
            frm_hwid_row,
            text="📋 คัดลอก HWID",
            command=self._copy_hwid,
            font=ctk.CTkFont(family=self.font_fam, size=12),
            width=110
        )
        btn_copy.pack(side="right")

        # License Key Input Card
        frm_key = ctk.CTkFrame(self, corner_radius=8)
        frm_key.pack(fill="x", padx=20, pady=8, ipady=6)

        ctk.CTkLabel(
            frm_key,
            text="ระบุรหัส License Key:",
            font=ctk.CTkFont(family=self.font_fam, size=12, weight="bold")
        ).pack(anchor="w", padx=14, pady=(6, 2))

        frm_key_row = ctk.CTkFrame(frm_key, fg_color="transparent")
        frm_key_row.pack(fill="x", padx=14, pady=4)

        current_key = self.config_mgr.get_setting("license_key", "")
        self.entry_key = ctk.CTkEntry(
            frm_key_row,
            font=ctk.CTkFont(family="Consolas", size=11),
            placeholder_text="วางรหัส License Key ที่นี่...",
            show="*"
        )
        if current_key:
            self.entry_key.insert(0, current_key)
        self.entry_key.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_eye = ctk.CTkButton(
            frm_key_row,
            text="👁️",
            width=36,
            command=self._toggle_eye
        )
        self.btn_eye.pack(side="right")

        # Status badge
        trial = self.license_mgr.get_trial_status()
        t_color = "#38A169" if not trial["is_expired"] else "#E53E3E"
        t_msg = f"สถานะปัจจุบัน: ทดลองใช้ฟรีเหลือ {trial['days_left']} วัน (หมดอายุ {trial['expiry_date']})"
        if current_key:
            is_valid, msg, _ = self.license_mgr.verify_license_key(current_key)
            if is_valid:
                t_msg = f"สถานะปัจจุบัน: ✅ {msg}"
                t_color = "#38A169"

        self.lbl_status = ctk.CTkLabel(
            self,
            text=t_msg,
            font=ctk.CTkFont(family=self.font_fam, size=12, weight="bold"),
            text_color=t_color
        )
        self.lbl_status.pack(pady=10)

        # Buttons
        frm_btn = ctk.CTkFrame(self, fg_color="transparent")
        frm_btn.pack(fill="x", padx=20, pady=12)

        btn_activate = ctk.CTkButton(
            frm_btn,
            text="🔓 ปลดล็อกและบันทึกสิทธิ์ (Activate Key)",
            command=self._activate_key,
            font=ctk.CTkFont(family=self.font_fam, size=13, weight="bold"),
            fg_color="#2B6CB0",
            hover_color="#2C5282",
            height=38
        )
        btn_activate.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_cancel = ctk.CTkButton(
            frm_btn,
            text="ปิดหน้าต่าง",
            command=self.destroy,
            font=ctk.CTkFont(family=self.font_fam, size=12),
            fg_color="gray50",
            hover_color="gray40",
            width=100,
            height=38
        )
        btn_cancel.pack(side="right")

    def _copy_hwid(self):
        self.clipboard_clear()
        self.clipboard_append(self.hwid_str)
        messagebox.showinfo("คัดลอกสำเร็จ", "คัดลอก Machine HWID ลงใน Clipboard เรียบร้อยแล้ว")

    def _toggle_eye(self):
        if self.entry_key.cget("show") == "*":
            self.entry_key.configure(show="")
            self.btn_eye.configure(text="🙈")
        else:
            self.entry_key.configure(show="*")
            self.btn_eye.configure(text="👁️")

    def _activate_key(self):
        key = self.entry_key.get().strip()
        if not key:
            messagebox.showwarning("คำเตือน", "กรุณาระบุ License Key")
            return

        is_valid, msg, info = self.license_mgr.verify_license_key(key)
        if is_valid:
            self.config_mgr.set_setting("license_key", key)
            self.lbl_status.configure(text=f"สถานะ: ✅ {msg}", text_color="#38A169")
            messagebox.showinfo("เปิดใช้งานสำเร็จ", f"ปลดล็อกระบบสำเร็จสมบูรณ์!\n{msg}")
            if self.on_activated_callback:
                self.on_activated_callback()
            self.destroy()
        else:
            self.lbl_status.configure(text=f"สถานะ: ❌ {msg}", text_color="#E53E3E")
            messagebox.showerror("ไม่สามารถเปิดใช้งานได้", f"การเปิดใช้งานล้มเหลว:\n{msg}")
