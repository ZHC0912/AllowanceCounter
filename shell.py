"""shell.py — Main application shell: sidebar navigation and page router."""

import tkinter as tk
from tkinter import ttk

from constants import C, is_dark, set_theme

# Pages are imported lazily inside show() to avoid circular imports at module load
# and to keep shell.py free of page-level concerns.


class MainShell(tk.Frame):
    def __init__(self, master, uid: int, uname: str):
        super().__init__(master, bg=C['bg'])
        self.uid   = uid
        self.uname = uname
        self._active_btn  = None
        self._current_page = 'dashboard'
        self._build()
        self.show('dashboard')

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        self._build_sidebar()
        self.content = tk.Frame(self, bg=C['bg'])
        self.content.pack(side='right', fill='both', expand=True)

    def _build_sidebar(self):
        sb = tk.Frame(self, bg=C['sidebar'], width=260)
        sb.pack(side='left', fill='y')
        sb.pack_propagate(False)

        # Logo + title
        tk.Label(sb, text='💰', font=('Segoe UI', 28),
                 bg=C['sidebar'], fg=C['lt']).pack(pady=(24, 4))
        tk.Label(sb, text='Allowance Counter',
                 font=('Segoe UI', 12, 'bold'),
                 bg=C['sidebar'], fg=C['lt']).pack()

        # User badge
        badge = tk.Frame(sb, bg='#253347', padx=14, pady=12)
        badge.pack(fill='x', padx=14, pady=(18, 14))
        tk.Label(badge, text=f'👤  {self.uname}',
                 font=('Segoe UI', 11, 'bold'),
                 bg='#253347', fg='white').pack(anchor='w')

        # Navigation buttons
        nav_items = [
            ('dashboard',  '📊   Dashboard'),
            ('expenses',   '📝   Expenses'),
            ('categories', '🏷   Categories'),
            ('allowance',  '💵   Allowance'),
            ('settings',   '⚙️   Settings'),
        ]
        self._nav_btns: dict = {}
        for pid, label in nav_items:
            b = tk.Button(
                sb, text=label,
                command=lambda p=pid: self.show(p),
                bg=C['sidebar'], fg='white',
                font=('Segoe UI', 12),
                relief='flat', bd=0,
                anchor='w', padx=22, pady=13,
                cursor='hand2',
                activebackground=C['sidebar_hover'],
                activeforeground='white',
            )
            b.pack(fill='x')
            b.bind('<Enter>', lambda e, btn=b: btn.config(bg=C['sidebar_hover'])
                              if btn is not self._active_btn else None)
            b.bind('<Leave>', lambda e, btn=b: btn.config(bg=C['sidebar'])
                              if btn is not self._active_btn else None)
            self._nav_btns[pid] = b

        # Dark mode toggle (pushed to bottom)
        tk.Frame(sb, bg=C['sidebar']).pack(fill='y', expand=True)

        dm_frame = tk.Frame(sb, bg=C['sidebar'], padx=22, pady=8)
        dm_frame.pack(fill='x')
        tk.Label(dm_frame, text='🌙  Dark Mode',
                 font=('Segoe UI', 11),
                 bg=C['sidebar'], fg='#b2bec3').pack(side='left')
        self._dm_var = tk.BooleanVar(value=is_dark())
        tk.Checkbutton(
            dm_frame, variable=self._dm_var,
            command=self._toggle_dark,
            bg=C['sidebar'], activebackground=C['sidebar'],
            selectcolor=C['sidebar_act'],
            relief='flat', bd=0, cursor='hand2',
        ).pack(side='right')

        # Logout
        tk.Button(
            sb, text='🚪   Logout',
            command=self.master.do_logout,
            bg=C['sidebar'], fg='#b2bec3',
            font=('Segoe UI', 11),
            relief='flat', bd=0,
            anchor='w', padx=22, pady=13,
            cursor='hand2',
            activebackground=C['danger'],
            activeforeground='white',
        ).pack(fill='x')

    # ── Navigation ─────────────────────────────────────────────────────────────

    def show(self, pid: str):
        self._current_page = pid

        if self._active_btn:
            self._active_btn.config(bg=C['sidebar'])
        self._active_btn = self._nav_btns.get(pid)
        if self._active_btn:
            self._active_btn.config(bg=C['sidebar_act'])

        for w in self.content.winfo_children():
            w.destroy()

        # Lazy import to keep module boundaries clean
        page_cls = self._get_page_class(pid)
        page_cls(self.content, self.uid, self.uname).pack(fill='both', expand=True)

    @staticmethod
    def _get_page_class(pid: str):
        """Return the page Frame class for the given page id."""
        if pid == 'dashboard':
            from page_dashboard import DashboardPage
            return DashboardPage
        if pid == 'expenses':
            from page_expenses import ExpensesPage
            return ExpensesPage
        if pid == 'categories':
            from page_categories import CategoriesPage
            return CategoriesPage
        if pid == 'allowance':
            from page_allowance import AllowancePage
            return AllowancePage
        if pid == 'settings':
            from page_settings import SettingsPage
            return SettingsPage
        raise ValueError(f'Unknown page: {pid!r}')

    # ── Theme toggle ───────────────────────────────────────────────────────────

    def _toggle_dark(self):
        set_theme(self._dm_var.get())
        self.master._rebuild_shell(self.uid, self.uname, self._current_page)
