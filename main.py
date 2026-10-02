# -*- coding: utf-8 -*-
"""
Main Application Entry Point.
Soft4U Server Admin & Security Audit Suite.
Enterprise Architecture Standard (Ultimate 2026+)
"""

import sys
import os
import ctypes
import logging

# Add current folder to sys.path so modules resolve cleanly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from version import APP_ID, APP_TITLE, APP_VERSION
from app.core.single_instance import SingleInstanceLock
from app.ui.main_window import ServerAdminApp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("Main")


def main():
    # 1. Windows Taskbar Identity Standard
    if sys.platform == "win32":
        try:
            app_user_id = f"soft4uapp.{APP_ID}.v2026"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_user_id)
        except Exception:
            pass

    # 2. Single-Instance Mutex Check
    single_lock = SingleInstanceLock()
    if not single_lock.acquire():
        logger.warning("ตรวจพบโปรแกรมกำลังทำงานอยู่แล้ว นำหน้าต่างเดิมขึ้นมาแสดง")
        sys.exit(0)

    try:
        # 3. Launch Modern Desktop UI
        app = ServerAdminApp()
        app.mainloop()
    finally:
        # 4. Release Mutex
        single_lock.release()


if __name__ == "__main__":
    main()
