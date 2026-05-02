"""main.py — Application entry point. Instantiates the root window."""

import tkinter as tk
from tkinter import messagebox, ttk

from constants import C, set_theme
from database import init_db, apply_recurring_expenses
from page_login import LoginPage
from shell import MainShell


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        ttk.Style(self).theme_use('clam')      # consistent ttk look on Windows
        self.title('Allowance Counter')
        self.configure(bg=C['bg'])

        # Centre window on screen
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f'1920x1080+{max(0, (sw - 1920) // 2)}+{max(0, (sh - 1080) // 2)}')
        self.minsize(1280, 720)

        self.protocol('WM_DELETE_WINDOW', self._on_close)
        init_db()
        self._show_login()

    # ── Window events ──────────────────────────────────────────────────────────

    def _on_close(self):
        open_dialogs = [
            w for w in self.winfo_children()
            if isinstance(w, tk.Toplevel) and w.winfo_exists()
        ]
        if open_dialogs:
            if not messagebox.askyesno('Exit', 'You have an open dialog. Exit anyway?'):
                return
        self.destroy()

    # ── Page transitions ───────────────────────────────────────────────────────

    def _show_login(self):
        for w in self.winfo_children():
            w.destroy()
        LoginPage(self).pack(fill='both', expand=True)

    def after_login(self, uid: int, uname: str):
        apply_recurring_expenses(uid)
        for w in self.winfo_children():
            w.destroy()
        MainShell(self, uid, uname).pack(fill='both', expand=True)

    def _rebuild_shell(self, uid: int, uname: str, page: str = 'dashboard'):
        """Tear down and rebuild the shell to apply a theme change."""
        self.configure(bg=C['bg'])
        for w in self.winfo_children():
            w.destroy()
        shell = MainShell(self, uid, uname)
        shell.pack(fill='both', expand=True)
        shell.show(page)

    def do_logout(self):
        if messagebox.askyesno('Logout', 'Log out of your account?'):
            self._show_login()


if __name__ == '__main__':
    App().mainloop()
