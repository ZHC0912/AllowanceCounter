"""constants.py — Shared constants, theme colours, and theme management."""

import os
import sys

# ── Paths ──────────────────────────────────────────────────────────────────────

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, 'allowance.db')

MONTHS = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]

# ── Theme Palettes ─────────────────────────────────────────────────────────────

LIGHT = {
    'bg':            '#f0f4f8',
    'sidebar':       '#1a2535',
    'sidebar_hover': '#253347',
    'sidebar_act':   '#00a896',
    'card':          '#ffffff',
    'primary':       '#2d6cdf',
    'success':       '#00b894',
    'danger':        '#e17055',
    'warning':       '#fdcb6e',
    'lt':            '#ffffff',
    'dk':            '#2d3436',
    'muted':         '#636e72',
    'border':        '#dfe6e9',
    'row_alt':       '#f7f9fc',
    'tbl_hdr':       '#eef2f7',
    'entry_bg':      '#ffffff',
    'entry_fg':      '#2d3436',
    'toast_bg':      '#2d3436',
    'toast_fg':      '#ffffff',
    'progress_bg':   '#dfe6e9',
}

DARK = {
    'bg':            '#1e1e2e',
    'sidebar':       '#11111b',
    'sidebar_hover': '#1a1a2e',
    'sidebar_act':   '#00a896',
    'card':          '#2a2a3e',
    'primary':       '#74b9ff',
    'success':       '#55efc4',
    'danger':        '#ff7675',
    'warning':       '#ffeaa7',
    'lt':            '#cdd6f4',
    'dk':            '#cdd6f4',
    'muted':         '#9399b2',
    'border':        '#45475a',
    'row_alt':       '#313244',
    'tbl_hdr':       '#313244',
    'entry_bg':      '#313244',
    'entry_fg':      '#cdd6f4',
    'toast_bg':      '#cdd6f4',
    'toast_fg':      '#1e1e2e',
    'progress_bg':   '#45475a',
}

# Active theme dict — mutated at runtime by set_theme()
C: dict = dict(LIGHT)
_dark_mode: bool = False


def set_theme(dark: bool) -> None:
    """Switch the active theme. Mutates C in-place so all modules see the change."""
    global _dark_mode
    _dark_mode = dark
    C.update(DARK if dark else LIGHT)


def is_dark() -> bool:
    return _dark_mode
