# -*- coding: utf-8 -*-
"""
Soft4UApp Enterprise Secure Vault (Ultimate Master Edition 2026+)
Dual-Layer Encrypted Binary Configuration Vault:
1. Field-Level: AES-256-GCM (ENC:GCM:<Base64(Nonce 12B + Tag 16B + Ciphertext)>)
2. File-Level Binary Vault: zlib level 9 + AES-256-GCM with Magic Header \x89S4U\x02\x00\x00\x00
"""

import os
import sys
import json
import zlib
import base64
import secrets
import subprocess
import uuid
import hashlib
from typing import Optional, Dict, Any, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

_MASTER_SALT = b"Soft4UApp_Enterprise_Secure_Vault_2026_Salt"
_MASTER_PEPPER = b"Soft4UApp_DBTools_SuperSecret_VaultKey_v2"
MAGIC_HEADER = b"\x89S4U\x02\x00\x00\x00"

ASCII_BANNER = (
    b"/*\n"
    b"================================================================================\n"
    b"  [ Soft4UApp Enterprise Secure Vault - AES-256-GCM Authenticated Encryption ]\n"
    b"  WARNING: Proprietary Encrypted Binary. Only Soft4UApp Tool Can Decrypt This!\n"
    b"================================================================================\n"
    b"*/\n"
)


def get_machine_hwid() -> str:
    """Retrieve unique Hardware UUID of the current machine (Windows/Fallback)."""
    # 1. PowerShell CimInstance
    try:
        cmd = ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_ComputerSystemProduct).UUID"]
        out = subprocess.check_output(cmd, creationflags=0x08000000, timeout=3).decode("utf-8", errors="ignore").strip()
        if out and len(out) > 10 and "00000000" not in out:
            return out
    except Exception:
        pass

    # 2. Windows MachineGuid from Registry
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
                guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                if guid:
                    return str(guid).strip()
        except Exception:
            pass

    # 3. Fallback MAC + Hostname
    try:
        node_id = hex(uuid.getnode())
        comp_name = os.environ.get("COMPUTERNAME", "UNKNOWN_PC")
        return f"FALLBACK-{comp_name}-{node_id}"
    except Exception:
        return "DEFAULT_SERVER_ADMIN_HWID_2026"


class SecurityManager:
    """Enterprise-grade AES-256-GCM authenticated encryption manager for Vault & Credentials."""

    _cached_key: Optional[bytes] = None

    @classmethod
    def _get_derived_key(cls) -> bytes:
        if cls._cached_key is None:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=_MASTER_SALT,
                iterations=100000,
            )
            cls._cached_key = kdf.derive(_MASTER_PEPPER)
        return cls._cached_key

    @classmethod
    def encrypt_text(cls, plaintext: str) -> str:
        """
        Encrypt plaintext string using AES-256-GCM.
        Returns: ENC:GCM:<base64(nonce 12B + tag 16B + ciphertext)>
        """
        if not plaintext or not isinstance(plaintext, str) or plaintext.startswith("ENC:GCM:"):
            return plaintext
        try:
            aesgcm = AESGCM(cls._get_derived_key())
            nonce = secrets.token_bytes(12)
            ct_and_tag = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
            ciphertext, tag = ct_and_tag[:-16], ct_and_tag[-16:]
            combined = nonce + tag + ciphertext
            return f"ENC:GCM:{base64.b64encode(combined).decode('ascii')}"
        except Exception:
            return plaintext

    @classmethod
    def decrypt_text(cls, encrypted_str: str) -> str:
        """
        Decrypt AES-256-GCM encrypted string.
        Returns original plaintext.
        """
        if not encrypted_str or not isinstance(encrypted_str, str) or not encrypted_str.startswith("ENC:GCM:"):
            return encrypted_str
        try:
            b64_data = encrypted_str[len("ENC:GCM:"):]
            combined = base64.b64decode(b64_data.encode("ascii"))
            if len(combined) < 28:
                return encrypted_str
            nonce = combined[:12]
            tag = combined[12:28]
            ciphertext = combined[28:]
            aesgcm = AESGCM(cls._get_derived_key())
            plaintext_bytes = aesgcm.decrypt(nonce, ciphertext + tag, None)
            return plaintext_bytes.decode("utf-8")
        except Exception:
            return ""

    @classmethod
    def encrypt_vault_payload(cls, data: dict) -> bytes:
        """
        Layer 2: Compress dict with zlib level 9, encrypt with AES-256-GCM,
        and prepend Magic Header + ASCII banner.
        """
        json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        compressed = zlib.compress(json_bytes, level=9)
        aesgcm = AESGCM(cls._get_derived_key())
        nonce = secrets.token_bytes(12)
        ct_and_tag = aesgcm.encrypt(nonce, compressed, None)
        ciphertext, tag = ct_and_tag[:-16], ct_and_tag[-16:]
        return ASCII_BANNER + MAGIC_HEADER + nonce + tag + ciphertext

    @classmethod
    def decrypt_vault_payload(cls, raw_bytes: bytes) -> Optional[dict]:
        """
        Decrypt Layer 2 Binary Vault bytes back to dictionary.
        """
        try:
            if MAGIC_HEADER in raw_bytes:
                idx = raw_bytes.index(MAGIC_HEADER) + len(MAGIC_HEADER)
                payload = raw_bytes[idx:]
                if len(payload) < 28:
                    return None
                nonce = payload[:12]
                tag = payload[12:28]
                ciphertext = payload[28:]
                aesgcm = AESGCM(cls._get_derived_key())
                compressed = aesgcm.decrypt(nonce, ciphertext + tag, None)
                json_bytes = zlib.decompress(compressed)
                return json.loads(json_bytes.decode("utf-8"))
            else:
                # Plain JSON fallback
                return json.loads(raw_bytes.decode("utf-8"))
        except Exception:
            return None
