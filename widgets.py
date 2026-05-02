"""widgets.py — Reusable UI components: buttons, entries, toast, tooltip, progress bar."""

import tkinter as tk
from tkinter import ttk

from constants import C, is_dark


# ── Treeview style helper ──────────────────────────────────────────────────────

def apply_treeview_style(style_name: str, row_height: int = 36) -> ttk.Style:
    """Configure a theme-aware Treeview style. Uses clam to override OS defaults."""
    st = ttk.Style()
    try:
        st.theme_use('clam')
    except Exception:
        pass

    sel_bg = '#2d5a8e' if is_dark() else '#3a7bd5'

    st.configure(
        style_name,
        font=('Segoe UI', 11),
        rowheight=row_height,
        background=C['card'],
        fieldbackground=C['card'],
        foreground=C['dk'],
        borderwidth=0,
        relief='flat',
    )
    st.configure(
        f'{style_name}.Heading',
        font=('Segoe UI', 11, 'bold'),
        background=C['tbl_hdr'],
        foreground=C['dk'],
        relief='flat',
        borderwidth=1,
    )
    st.map(
        style_name,
        background=[('selected', sel_bg)],
        foreground=[('selected', '#ffffff')],
    )
    return st


# ── Button ─────────────────────────────────────────────────────────────────────

def mbtn(parent, text: str, cmd, color: str = 'primary', **kw) -> tk.Button:
    """Flat, themed button. color ∈ {'primary', 'success', 'danger', 'ghost'}."""
    success_fg = '#111111' if is_dark() else C['lt']
    palette = {
        'primary': (C['primary'], C['lt']),
        'success': (C['success'], success_fg),
        'danger':  (C['danger'],  C['lt']),
        'ghost':   (C['card'],    C['dk']),
    }
    bg, fg = palette.get(color, palette['primary'])
    return tk.Button(
        parent, text=text, command=cmd,
        bg=bg, fg=fg,
        font=('Segoe UI', 10, 'bold'),
        relief='flat', bd=0,
        padx=14, pady=7,
        cursor='hand2',
        activebackground=bg, activeforeground=fg,
        **kw,
    )


# ── Padded single-line entry ───────────────────────────────────────────────────

class _PaddedEntry(tk.Frame):
    """
    A tk.Text-backed single-line entry with true internal padding.
    Supports show='•' for password masking and textvariable binding.
    """

    def __init__(self, parent, show=None, textvariable=None, width=None, **kw):
        kw.pop('width', None)
        border_col = '#ffffff' if is_dark() else C['border']
        super().__init__(parent, bg=border_col, highlightthickness=0, bd=0)

        inner = tk.Frame(self, bg=C['entry_bg'], bd=0)
        inner.pack(fill='both', expand=True, padx=1, pady=1)

        self._show = show
        self._textvariable = textvariable
        self._blocked = False

        self._txt = tk.Text(
            inner,
            font=('Segoe UI', 11),
            bg=C['entry_bg'], fg=C['entry_fg'],
            insertbackground=C['entry_fg'],
            relief='flat', bd=0,
            padx=10, pady=4,
            height=1, wrap='none',
            undo=False,
            selectbackground=C['primary'],
            selectforeground='white',
        )
        self._txt.pack(fill='both', expand=True)

        # Single-line enforcement
        self._txt.bind('<Return>',    lambda e: 'break')
        self._txt.bind('<KP_Enter>',  lambda e: 'break')
        self._txt.bind('<Tab>',       lambda e: (self._txt.tk_focusNext().focus(), 'break'))

        if show:
            self._real = ''
            self._txt.bind('<Key>',       self._mask_key)
            self._txt.bind('<BackSpace>', self._mask_bs)
            self._txt.bind('<<Paste>>',   lambda e: 'break')

        if textvariable is not None:
            textvariable.trace_add('write', self._var_to_txt)
            self._txt.bind('<<Modified>>', self._txt_to_var)

        self._txt.bind('<FocusIn>',  lambda e: self.config(bg=C['primary']))
        self._txt.bind('<FocusOut>', lambda e: self.config(bg=border_col))

    # ── password masking ──────────────────────────────────────────────

    def _mask_key(self, event):
        if event.char and event.char.isprintable():
            pos = self._char_pos(self._txt.index('insert'))
            self._real = self._real[:pos] + event.char + self._real[pos:]
            self._txt.insert('insert', self._show)
            return 'break'

    def _mask_bs(self, event):
        if self._real:
            pos = self._char_pos(self._txt.index('insert'))
            if pos > 0:
                self._real = self._real[:pos - 1] + self._real[pos:]
                self._txt.delete('insert-1c', 'insert')
        return 'break'

    @staticmethod
    def _char_pos(idx) -> int:
        return int(str(idx).split('.')[1])

    # ── textvariable sync ─────────────────────────────────────────────

    def _var_to_txt(self, *_):
        if self._blocked:
            return
        self._blocked = True
        val = self._textvariable.get()
        self._txt.delete('1.0', 'end')
        if self._show:
            self._real = val
            self._txt.insert('1.0', self._show * len(val))
        else:
            self._txt.insert('1.0', val)
        self._txt.edit_modified(False)
        self._blocked = False

    def _txt_to_var(self, *_):
        if not self._txt.edit_modified():
            return
        if self._blocked:
            return
        self._blocked = True
        if self._textvariable is not None and not self._show:
            self._textvariable.set(self._txt.get('1.0', 'end-1c'))
        self._txt.edit_modified(False)
        self._blocked = False

    # ── public Entry-compatible API ───────────────────────────────────

    def get(self) -> str:
        return self._real if self._show else self._txt.get('1.0', 'end-1c')

    def delete(self, a=None, b=None):
        if self._show:
            self._real = ''
        self._txt.delete('1.0', 'end')

    def insert(self, idx, val: str):
        self._txt.insert('end', val)

    def focus(self):
        self._txt.focus()

    def bind(self, seq, func, add=None):
        self._txt.bind(seq, func, add)

    def pack(self, **kw):
        kw.pop('ipadx', None)
        kw.pop('ipady', None)
        super().pack(**kw)

    def grid(self, **kw):
        kw.pop('ipadx', None)
        kw.pop('ipady', None)
        super().grid(**kw)


def mentry(parent, **kw) -> _PaddedEntry:
    """Factory function — returns a _PaddedEntry."""
    return _PaddedEntry(parent, **kw)


# ── Label shorthand ────────────────────────────────────────────────────────────

def flabel(parent, text: str, font=None, bg=None, fg=None, **kw) -> tk.Label:
    return tk.Label(
        parent, text=text,
        font=font or ('Segoe UI', 11),
        bg=bg or C['bg'],
        fg=fg or C['dk'],
        **kw,
    )


# ── Toast notification ─────────────────────────────────────────────────────────

class Toast:
    """Brief pop-up notification with optional Undo callback."""

    _instance = None

    @classmethod
    def show(cls, root, message: str, undo_cb=None, duration: int = 4000):
        if cls._instance:
            try:
                cls._instance.destroy()
            except Exception:
                pass
        cls._instance = cls._make(root, message, undo_cb, duration)

    @staticmethod
    def _make(root, message: str, undo_cb, duration: int):
        t = tk.Toplevel(root)
        t.overrideredirect(True)
        t.attributes('-topmost', True)
        t.configure(bg=C['toast_bg'])

        frame = tk.Frame(t, bg=C['toast_bg'], padx=16, pady=10)
        frame.pack()
        tk.Label(frame, text=message, font=('Segoe UI', 11),
                 bg=C['toast_bg'], fg=C['toast_fg']).pack(side='left', padx=(0, 12))

        if undo_cb:
            def do_undo():
                undo_cb()
                t.destroy()

            tk.Button(
                frame, text='UNDO', command=do_undo,
                bg=C['primary'], fg='white',
                font=('Segoe UI', 10, 'bold'),
                relief='flat', bd=0, padx=10, pady=4, cursor='hand2',
            ).pack(side='left')

        root.update_idletasks()
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        t.update_idletasks()
        w, h = t.winfo_width(), t.winfo_height()
        t.geometry(f'+{sw - w - 30}+{sh - h - 60}')
        root.after(duration, lambda: t.destroy() if t.winfo_exists() else None)
        return t


# ── Tooltip ────────────────────────────────────────────────────────────────────

class Tooltip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind('<Enter>', self._show)
        widget.bind('<Leave>', self._hide)

    def _show(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.overrideredirect(True)
        self.tip.attributes('-topmost', True)
        tk.Label(
            self.tip, text=self.text,
            font=('Segoe UI', 9),
            bg='#2d3436', fg='white',
            padx=10, pady=6,
            wraplength=220, justify='left',
        ).pack()
        self.tip.geometry(f'+{x}+{y}')

    def _hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ── Budget progress bar ────────────────────────────────────────────────────────

class BudgetBar(tk.Frame):
    """Horizontal progress bar for budget utilisation."""

    def __init__(self, parent, pct: float, color: str, **kw):
        super().__init__(parent, bg=C['card'], **kw)
        pct = max(0.0, min(pct, 100.0))
        bar_bg = tk.Frame(self, bg=C['progress_bg'], height=10)
        bar_bg.pack(fill='x', pady=(6, 2))
        bar_bg.pack_propagate(False)
        tk.Frame(bar_bg, bg=color, height=10).place(relwidth=pct / 100, relheight=1)
