"""page_settings.py — Settings and profile management page."""

import tkinter as tk
import tkinter.simpledialog as sd
from tkinter import messagebox

from constants import C
from database import db_one, db_run, hash_pw
from widgets import mbtn, mentry


class SettingsPage(tk.Frame):
    def __init__(self, master, uid: int, uname: str):
        super().__init__(master, bg=C['bg'])
        self.uid   = uid
        self.uname = uname
        self._build()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        tk.Label(self, text='Settings & Profile',
                 font=('Segoe UI', 20, 'bold'),
                 bg=C['bg'], fg=C['dk']).pack(anchor='w', padx=32, pady=(22, 16))

        body = tk.Frame(self, bg=C['bg'], padx=32)
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        self._build_profile_card(body)
        self._build_danger_card(body)

    def _build_profile_card(self, body):
        pc = tk.Frame(body, bg=C['card'], padx=26, pady=24)
        pc.grid(row=0, column=0, sticky='nsew', padx=(0, 16), pady=(0, 16))

        tk.Label(pc, text='👤  Profile',
                 font=('Segoe UI', 14, 'bold'),
                 bg=C['card'], fg=C['dk']).pack(anchor='w', pady=(0, 14))
        tk.Label(pc, text='Username',
                 font=('Segoe UI', 10, 'bold'),
                 bg=C['card'], fg=C['dk'], anchor='w').pack(fill='x')
        tk.Label(pc, text=self.uname,
                 font=('Segoe UI', 14),
                 bg=C['card'], fg=C['primary']).pack(anchor='w', pady=(2, 16))

        tk.Frame(pc, bg=C['border'], height=1).pack(fill='x', pady=(0, 16))

        tk.Label(pc, text='Change Password',
                 font=('Segoe UI', 12, 'bold'),
                 bg=C['card'], fg=C['dk']).pack(anchor='w', pady=(0, 10))

        def lbl(t):
            tk.Label(pc, text=t, font=('Segoe UI', 10, 'bold'),
                     bg=C['card'], fg=C['dk'], anchor='w').pack(fill='x', pady=(8, 3))

        lbl('Current Password')
        self._cp = mentry(pc, show='•')
        self._cp.pack(fill='x', ipady=5)

        lbl('New Password')
        self._np = mentry(pc, show='•')
        self._np.pack(fill='x', ipady=5)

        lbl('Confirm New Password')
        self._cnp = mentry(pc, show='•')
        self._cnp.pack(fill='x', ipady=5)

        tk.Frame(pc, height=12, bg=C['card']).pack()
        mbtn(pc, '🔒  Update Password', self._change_pw, 'primary').pack(anchor='w')

        self._pw_status = tk.Label(pc, text='', font=('Segoe UI', 10),
                                   bg=C['card'], fg=C['success'])
        self._pw_status.pack(anchor='w', pady=(8, 0))

    def _build_danger_card(self, body):
        dc = tk.Frame(body, bg=C['card'], padx=26, pady=24)
        dc.grid(row=0, column=1, sticky='nsew', pady=(0, 16))

        tk.Label(dc, text='⚠️  Danger Zone',
                 font=('Segoe UI', 14, 'bold'),
                 bg=C['card'], fg=C['danger']).pack(anchor='w', pady=(0, 14))
        tk.Frame(dc, bg=C['border'], height=1).pack(fill='x', pady=(0, 16))

        # Delete all expenses
        tk.Label(dc, text='Delete All My Expenses',
                 font=('Segoe UI', 12, 'bold'),
                 bg=C['card'], fg=C['dk']).pack(anchor='w')
        tk.Label(dc,
                 text='Permanently removes all expense records. Cannot be undone.',
                 font=('Segoe UI', 10), bg=C['card'], fg=C['muted'],
                 wraplength=280, justify='left').pack(anchor='w', pady=(4, 10))
        mbtn(dc, '🗑  Delete All Expenses', self._delete_all_expenses,
             'danger', width=20).pack(anchor='w')

        tk.Frame(dc, bg=C['border'], height=1).pack(fill='x', pady=(16, 16))

        # Delete account
        tk.Label(dc, text='Delete My Account',
                 font=('Segoe UI', 12, 'bold'),
                 bg=C['card'], fg=C['dk']).pack(anchor='w')
        tk.Label(dc,
                 text='Permanently deletes your account and all data.',
                 font=('Segoe UI', 10), bg=C['card'], fg=C['muted'],
                 wraplength=280, justify='left').pack(anchor='w', pady=(4, 10))
        mbtn(dc, '☠  Delete Account', self._delete_account,
             'danger', width=20).pack(anchor='w')

    # ── Actions ────────────────────────────────────────────────────────────────

    def _change_pw(self):
        cp  = self._cp.get()
        np  = self._np.get()
        cnp = self._cnp.get()
        if not cp or not np or not cnp:
            messagebox.showerror('Error', 'Fill in all password fields.')
            return
        if not db_one('SELECT id FROM users WHERE id=? AND password=?',
                      (self.uid, hash_pw(cp))):
            messagebox.showerror('Error', 'Current password is incorrect.')
            return
        if len(np) < 4:
            messagebox.showerror('Error', 'New password must be ≥ 4 characters.')
            return
        if np != cnp:
            messagebox.showerror('Error', 'New passwords do not match.')
            return
        db_run('UPDATE users SET password=? WHERE id=?', (hash_pw(np), self.uid))
        self._cp.delete()
        self._np.delete()
        self._cnp.delete()
        self._pw_status.config(text='✓  Password updated successfully!', fg=C['success'])

    def _delete_all_expenses(self):
        if messagebox.askyesno(
            'Confirm',
            'Delete ALL your expense records? This cannot be undone.',
        ):
            db_run('DELETE FROM expenses WHERE user_id=?', (self.uid,))
            messagebox.showinfo('Done', 'All expenses deleted.')

    def _delete_account(self):
        pw = sd.askstring(
            'Confirm Deletion',
            'Enter your password to confirm:',
            show='•', parent=self,
        )
        if pw is None:
            return
        if not db_one('SELECT id FROM users WHERE id=? AND password=?',
                      (self.uid, hash_pw(pw))):
            messagebox.showerror('Error', 'Incorrect password.')
            return
        if not messagebox.askyesno(
            'Final Confirmation',
            'This will permanently delete your account and ALL data. Continue?',
        ):
            return
        db_run('DELETE FROM expenses   WHERE user_id=?', (self.uid,))
        db_run('DELETE FROM allowances WHERE user_id=?', (self.uid,))
        db_run('DELETE FROM categories WHERE user_id=?', (self.uid,))
        db_run('DELETE FROM users WHERE id=?', (self.uid,))
        self.winfo_toplevel().do_logout()
