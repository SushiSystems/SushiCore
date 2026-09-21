"""The Sushi Systems mark and wordmark as data: palettes and pixel grids.

Mark keys: n nori, r rice, a amber, g green, h inner white glow, H outer white glow.
Wordmark keys: w the terminal's own foreground, a amber. "." is transparent.
Only ui/logo.py reads this module.
"""

from __future__ import annotations

K_TRANSPARENT = "."
K_FOREGROUND_KEY = "w"

K_PALETTE: dict[str, str] = {
    "n": "#1a1c20",
    "r": "#f4f4f4",
    "a": "#f0a500",
    "g": "#4caf50",
}

K_GLOW_PALETTE: dict[str, str] = {
    "h": "#8c8c8c",
    "H": "#3d3d3d",
}

K_MARK_PIXELS: tuple[str, ...] = (
    ".....HHHHHHHH.....",
    "...HHhhhhhhhhH....",
    "..HhhnnnnnnnnhH...",
    ".HhnrrrrrrrnnnhH..",
    ".HhrrrrrrrrrnnnhH.",
    "HhnrraaaaarrrnnhH.",
    "HhnraaaaaaarrnnnhH",
    "HhnraaaaaaaarnnnhH",
    "HhnraaaaaaaarnnnhH",
    "HhnraaaaaaaarnnnhH",
    "HhnrragggggrrnnnhH",
    "HhnrrrrggrrrrnnhH.",
    ".HhnrrrrrrrrnnhH..",
    "..HhhnnnnnnnhhH...",
    "...HHhhhhhhhHH....",
    ".....HHHHHHH......",
)

K_WORDMARK_PIXELS: tuple[str, ...] = (
    ".wwwww.ww..ww..wwwww.ww..ww.ww....................",
    "ww.....ww..ww.ww.....ww..ww.ww....................",
    "ww.....ww..ww.ww.....ww..ww.ww....................",
    ".wwww..ww..ww..wwww..wwwwww.ww....................",
    "....ww.ww..ww.....ww.ww..ww.ww....................",
    "....ww.ww..ww.....ww.ww..ww.ww....................",
    "wwwww...wwww..wwwww..ww..ww.ww....................",
    "..................................................",
    "..................................................",
    ".aaaaa.aa..aa..aaaaa.aaaaaa.aaaaaa.aa....aa..aaaaa",
    "aa.....aa..aa.aa.......aa...aa.....aaa..aaa.aa....",
    "aa......aaaa..aa.......aa...aa.....aaaaaaaa.aa....",
    ".aaaa....aa....aaaa....aa...aaaa...aa.aa.aa..aaaa.",
    "....aa...aa.......aa...aa...aa.....aa.aa.aa.....aa",
    "....aa...aa.......aa...aa...aa.....aa....aa.....aa",
    "aaaaa....aa...aaaaa....aa...aaaaaa.aa....aa.aaaaa.",
)
