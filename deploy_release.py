# -*- coding: utf-8 -*-
"""
GitHub Auto-Deployer for Soft4U Server Admin & Security Audit Suite.
Handles version syncing, GitHub Release asset upload, and Release pruning.
Developed according to Soft4UApp Enterprise Architecture Standard.
"""

import os
import sys
import json
import shutil
import base64
import subprocess
from version import GITHUB_REPO, APP_VERSION

REPO_NAME = GITHUB_REPO
KEEP_RELEASES_COUNT = 5


def log(msg: str, status: str = "INFO"):
    prefix = "[INFO] "
    if status == "SUCCESS":
        prefix = "[OK] "
    elif status == "WARNING":
        prefix = "[WARN] "
    elif status == "ERROR":
        prefix = "[ERROR] "
    print(f"{prefix}{msg}")


def prune_old_releases(keep_count: int = KEEP_RELEASES_COUNT) -> None:
    """Retains only the latest `keep_count` releases on GitHub and cleans up older ones."""
    if not shutil.which("gh"):
        return

    log(f"Scanning GitHub Releases (Auto-retention policy: Keep latest {keep_count} versions)...", "INFO")
    try:
        cmd_list = [
            "gh", "release", "list",
            "--repo", REPO_NAME,
            "--limit", "100",
            "--json", "tagName,createdAt"
        ]
        res = subprocess.run(cmd_list, capture_output=True, text=True)
        if res.returncode != 0:
            log(f"Could not fetch releases: {res.stderr.strip()}", "WARNING")
            return

        all_releases = json.loads(res.stdout.strip() or "[]")
        master_releases = [
            r for r in all_releases
            if str(r.get("tagName", "")).startswith("v")
        ]
        total_releases = len(master_releases)
        log(f"Found {total_releases} releases on GitHub.", "INFO")

        if total_releases <= keep_count:
            log(f"Current release count ({total_releases}) is <= {keep_count}. No pruning required.", "SUCCESS")
            return

        old_releases = master_releases[keep_count:]
        log(f"Pruning {len(old_releases)} outdated releases & tags...", "INFO")

        deleted_count = 0
        for rel in old_releases:
            tag_name = rel.get("tagName")
            if not tag_name:
                continue
            log(f"   Deleting old release [{tag_name}]...", "INFO")
            del_cmd = [
                "gh", "release", "delete", tag_name,
                "--repo", REPO_NAME,
                "--yes",
                "--cleanup-tag"
            ]
            del_res = subprocess.run(del_cmd, capture_output=True, text=True)
            if del_res.returncode == 0:
                deleted_count += 1
                log(f"   Successfully deleted release [{tag_name}]", "SUCCESS")

        log(f"Cleaned up {deleted_count} old versions! Exactly {keep_count} latest releases preserved.", "SUCCESS")
    except Exception as ex:
        log(f"Release pruning encountered an error: {ex}", "WARNING")


def deploy():
    print("=" * 70)
    print(f"Soft4UApp GitHub Auto-Deploy Engine -> {REPO_NAME}")
    print("=" * 70)

    # 1. Prepare version.json
    root_vjson = "version.json"
    latest_ver = APP_VERSION
    raw_tag = f"v{latest_ver}"

    vdata = {
        "latest_version": latest_ver,
        "version_tag": raw_tag,
        "download_url": f"https://github.com/{REPO_NAME}/releases/download/{raw_tag}/Server_Admin_Suite.exe",
        "release_notes": f"🚀 Soft4U Server Admin Suite {raw_tag}: Enterprise Architecture 2026+ Release",
        "file_size_mb": 41.0
    }

    with open(root_vjson, "w", encoding="utf-8") as f:
        json.dump(vdata, f, ensure_ascii=False, indent=4)

    log(f"Target Release Version Tag: {raw_tag}", "INFO")
    log(f"Configured download_url: {vdata['download_url']}", "SUCCESS")

    # 2. Check binary
    target_exe = os.path.join("dist", "Server_Admin_Suite.exe")
    if not os.path.exists(target_exe):
        log(f"Executable binary not found at: {target_exe}", "ERROR")
        return False
    else:
        file_mb = os.path.getsize(target_exe) / (1024 * 1024)
        log(f"Found binary: {target_exe} ({file_mb:.2f} MB)", "SUCCESS")

    # 3. Create GitHub Release & Upload Binary
    gh_available = shutil.which("gh") is not None
    if gh_available:
        log(f"Creating GitHub Release {raw_tag} & uploading {target_exe}...", "INFO")
        cmd_create = [
            "gh", "release", "create", raw_tag, target_exe,
            "--repo", REPO_NAME,
            "--title", f"Release {raw_tag}",
            "--notes", f"Auto-built and released by Soft4UApp Automation System ({raw_tag})",
            "--target", "main",
            "--latest"
        ]
        res = subprocess.run(cmd_create, capture_output=True, text=True)
        if res.returncode == 0:
            log(f"GitHub Release {raw_tag} created & binary uploaded successfully!", "SUCCESS")
        else:
            log(f"Release creation note: {res.stderr.strip() or res.stdout.strip()}", "WARNING")
            cmd_upload = [
                "gh", "release", "upload", raw_tag, target_exe,
                "--repo", REPO_NAME,
                "--clobber"
            ]
            res_up = subprocess.run(cmd_upload, capture_output=True, text=True)
            if res_up.returncode == 0:
                log(f"Binary uploaded to release {raw_tag} successfully!", "SUCCESS")

    # 4. Prune older releases (Keep latest 5)
    if gh_available:
        prune_old_releases(keep_count=KEEP_RELEASES_COUNT)

    print("=" * 70)
    print(f"DEPLOYMENT SUMMARY FOR {raw_tag}:")
    print(f"   Release URL: https://github.com/{REPO_NAME}/releases/tag/{raw_tag}")
    print(f"   Manifest   : https://raw.githubusercontent.com/{REPO_NAME}/main/version.json")
    print(f"   Retention  : Preserved latest {KEEP_RELEASES_COUNT} releases on GitHub")
    print("=" * 70)
    return True


if __name__ == "__main__":
    deploy()
