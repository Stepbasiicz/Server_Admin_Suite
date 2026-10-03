# -*- coding: utf-8 -*-
"""
Soft4U Server Admin & Security Audit Suite - Automated EXE Builder.
Compiles standalone single-file Windows executable using PyInstaller.
"""

import os
import sys
import glob
import shutil
import subprocess
from datetime import datetime

# Handle Windows Thai CP874 Console Unicode issues
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BUILD_TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
APP_VERSION = datetime.now().strftime("%y%m%d.%H%M")
BUILD_TAG = f"v{APP_VERSION}"
EXE_NAME = "Server_Admin_Suite"


def cleanup_build_artifacts():
    """Clean temporary spec and build folders."""
    for spec_file in glob.glob("*.spec"):
        try:
            os.remove(spec_file)
        except Exception:
            pass

    for folder in ["build", "__pycache__", os.path.join("dist", EXE_NAME)]:
        if os.path.isdir(folder):
            try:
                shutil.rmtree(folder)
            except Exception:
                pass


def build():
    print("=" * 70)
    print(f"[BUILD ENGINE] Compiling {EXE_NAME}.exe [{BUILD_TAG}]")
    print(f"   Python Executable: {sys.executable}")
    print("=" * 70)

    # 1. Clean up
    cleanup_build_artifacts()

    # 2. Ensure dist and reports exist
    os.makedirs("dist", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    # 3. Construct PyInstaller Command
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onefile",
        f"--name={EXE_NAME}",
        "--collect-all", "customtkinter",
        "--collect-all", "reportlab",
        "--hidden-import", "paramiko",
        "--hidden-import", "pymysql",
        "--hidden-import", "cryptography",
        "--hidden-import", "reportlab.platypus",
        "--hidden-import", "reportlab.lib.colors",
        "--hidden-import", "reportlab.lib.pagesizes",
        "--hidden-import", "reportlab.lib.styles",
        "main.py"
    ]

    print("\n[PyInstaller] Executing build command (Single-File Standalone EXE)...")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        exe_path = os.path.abspath(os.path.join("dist", f"{EXE_NAME}.exe"))
        print("\n" + "=" * 70)
        print("[SUCCESS] Build Completed Successfully!")
        print(f"   Single Executable Location: {exe_path}")
        print("=" * 70)

        # If D:\pp\admin tools exists, update it automatically
        test_dir = r"D:\pp\admin tools"
        if os.path.exists(test_dir):
            try:
                dest = os.path.join(test_dir, f"{EXE_NAME}.exe")
                shutil.copy2(exe_path, dest)
                print(f"[AUTO-COPY] Copied standalone Single EXE to: {dest}")
            except Exception as e:
                print(f"[AUTO-COPY WARNING] Could not copy to {test_dir}: {e}")
    else:
        print("\n" + "=" * 70)
        print(f"[FAILED] Build failed with exit code: {result.returncode}")
        print("=" * 70)
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()
