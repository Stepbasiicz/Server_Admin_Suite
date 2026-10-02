# -*- coding: utf-8 -*-
"""
Dynamic Thai Font Resolver and Safe Font Dictionary.
Ensures crisp, clean typography on Windows CustomTkinter across Thai text.
"""

import sys
import tkinter as tk
from tkinter import font as tkfont
from typing import Dict, Any, Tuple

PREFERRED_FONTS = [
    "Leelawadee UI",
    "Sarabun",
    "Tahoma",
    "Segoe UI",
    "Cordia New",
    "Arial"
]


class SafeFontDict(dict):
    """Dictionary for fonts that never raises KeyError and falls back cleanly."""
    def __init__(self, fallback_family: str = "Segoe UI"):
        super().__init__()
        self.fallback_family = fallback_family

    def __missing__(self, key: str) -> Tuple[str, int]:
        return (self.fallback_family, 13)


class FontManager:
    """Detects available Thai fonts and provides consistent font tuples."""

    _resolved_font: str = "Segoe UI"
    _fonts: SafeFontDict = SafeFontDict()

    @classmethod
    def resolve_best_font(cls, master=None) -> str:
        """Find the best installed font supporting Thai."""
        try:
            if master:
                available = set(tkfont.families(master))
            else:
                available = set(tkfont.families())

            for font_name in PREFERRED_FONTS:
                if font_name in available:
                    cls._resolved_font = font_name
                    break
        except Exception:
            cls._resolved_font = "Leelawadee UI" if sys.platform == "win32" else "Segoe UI"

        cls._init_font_dict()
        return cls._resolved_font

    @classmethod
    def _init_font_dict(cls):
        fam = cls._resolved_font
        cls._fonts = SafeFontDict(fam)
        cls._fonts.update({
            "title": (fam, 20, "bold"),
            "header": (fam, 16, "bold"),
            "subheader": (fam, 14, "bold"),
            "body": (fam, 12),
            "body_bold": (fam, 12, "bold"),
            "small": (fam, 10),
            "code": ("Consolas", 11),
            "code_bold": ("Consolas", 11, "bold"),
            "status": (fam, 11)
        })

    @classmethod
    def get_font(cls, name: str = "body") -> Tuple[Any, ...]:
        if not cls._fonts:
            cls.resolve_best_font()
        return cls._fonts[name]

    @classmethod
    def font_family(cls) -> str:
        if not cls._fonts:
            cls.resolve_best_font()
        return cls._resolved_font
