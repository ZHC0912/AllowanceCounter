"""page_login.py — Login and registration screen."""

import tkinter as tk
from tkinter import messagebox

from constants import C
from database import get_user_by_credentials, create_user
from widgets import mentry


class LoginPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=C['bg'])
        self._build()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        # Left branding panel
        left = tk.Frame(self, bg=C['sidebar'], width=500)
        left.pack(side='left', fill='y')
        left.pack_propagate(False)

        brand = tk.Frame(left, bg=C['sidebar'])
        brand.place(relx=0.5, rely=0.5, anchor='center')
        tk.Label(brand, text='💰', font=('Segoe UI', 72),
                 bg=C['sidebar'], fg=C['lt']).pack()
        tk.Label(brand, text='Allowance Counter',
                 font=('Segoe UI', 26, 'bold'),
                 bg=C['sidebar'], fg=C['lt']).pack(pady=(8, 4))
        tk.Label(brand, text='Track  •  Budget  •  Save',
                 font=('Segoe UI', 13),
                 bg=C['sidebar'], fg='#74b9ff').pack()

        # Right form panel
        right = tk.Frame(self, bg=C['bg'])
        right.pack(side='right', fill='both', expand=True)

        holder = tk.Frame(right, bg=C['bg'], width=420, height=420)
        holder.place(relx=0.5, rely=0.5, anchor='center')
        holder.pack_propagate(False)

        tk.Label(holder, text='Welcome Back!',
                 font=('Segoe UI', 22, 'bold'),
                 bg=C['bg'], fg=C['dk']).pack(pady=(0, 4))
        tk.Label(holder, text='Sign in to manage your allowance',
                 font=('Segoe UI', 11),
                 bg=C['bg'], fg=C['muted']).pack(pady=(0, 24))

        # Login / Register tabs
        tab_row = tk.Frame(holder, bg=C['border'], padx=2, pady=2)
        tab_row.pack(fill='x', pady=(0, 20))
        self._tbtn_login = tk.Button(
            tab_row, text='Login',
            command=lambda: self._tab('login'),
            font=('Segoe UI', 11, 'bold'), relief='flat', bd=0,
            bg=C['primary'], fg='white', padx=20, pady=8, cursor='hand2')
        self._tbtn_login.pack(side='left', fill='x', expand=True)
        self._tbtn_reg = tk.Button(
            tab_row, text='Register',
            command=lambda: self._tab('register'),
            font=('Segoe UI', 11, 'bold'), relief='flat', bd=0,
            bg=C['card'], fg=C['dk'], padx=20, pady=8, cursor='hand2')
        self._tbtn_reg.pack(side='left', fill='x', expand=True)

        self._form_area = tk.Frame(holder, bg=C['bg'])
        self._form_area.pack(fill='x')
        self._lf = self._make_login(self._form_area)
        self._rf = self._make_reg(self._form_area)
        self._lf.pack(fill='x')

    # ── Tab switching ──────────────────────────────────────────────────────────

    def _tab(self, which: str):
        if which == 'login':
            self._tbtn_login.config(bg=C['primary'], fg='white')
            self._tbtn_reg.config(bg=C['card'], fg=C['dk'])
            self._rf.pack_forget()
            self._lf.pack(fill='x')
        else:
            self._tbtn_reg.config(bg=C['primary'], fg='white')
            self._tbtn_login.config(bg=C['card'], fg=C['dk'])
            self._lf.pack_forget()
            self._rf.pack(fill='x')

    # ── Form builders ──────────────────────────────────────────────────────────

    def _field(self, parent, label: str, show=None, placeholder: str = '') -> tk.Entry:
        tk.Label(parent, text=label,
                 font=('Segoe UI', 10, 'bold'),
                 bg=C['bg'], fg=C['dk'], anchor='w').pack(fill='x', pady=(10, 3))

        # Use plain tk.Entry so fg works reliably
        e = tk.Entry(
            parent,
            font=('Segoe UI', 11),
            bg=C['card'],
            fg=C['dk'],
            insertbackground=C['dk'],
            relief='flat',
            bd=6,
        )
        e.pack(fill='x', ipady=6)

        if placeholder:
            e.insert(0, placeholder)
            e.config(fg=C['muted'])

            def on_focus_in(event, widget=e, ph=placeholder, s=show):
                if widget.get() == ph:
                    widget.delete(0, 'end')
                    widget.config(fg=C['dk'])
                    if s:
                        widget.config(show=s)

            def on_focus_out(event, widget=e, ph=placeholder, s=show):
                if not widget.get():
                    if s:
                        widget.config(show='')
                    widget.insert(0, ph)
                    widget.config(fg=C['muted'])

            e.bind('<FocusIn>', on_focus_in)
            e.bind('<FocusOut>', on_focus_out)

        elif show:
            e.config(show=show)

        return e

    def _make_login(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=C['bg'])
        self.lu = self._field(f, 'Username')
        self.lp = self._field(f, 'Password', show='•')
        self.lu.bind('<Return>', lambda e: self.lp.focus())
        self.lp.bind('<Return>', lambda e: self._do_login())
        tk.Frame(f, height=16, bg=C['bg']).pack()
        tk.Button(
            f, text='  Login  →', command=self._do_login,
            bg=C['primary'], fg=C['lt'],
            font=('Segoe UI', 10, 'bold'), relief='flat', bd=0,
            padx=14, pady=7, cursor='hand2',
            activebackground=C['primary'], activeforeground=C['lt'],
        ).pack(fill='x', ipady=5)
        return f

    def _make_reg(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=C['bg'])
        self.ru = self._field(f, 'Username', placeholder='min 3 characters')
        self.rp = self._field(f, 'Password', show='•', placeholder='min 4 characters')
        self.rp.bind('<Return>', lambda e: self._do_reg())
        tk.Frame(f, height=16, bg=C['bg']).pack()
        tk.Button(
            f, text='  Register  →', command=self._do_reg,
            bg=C['success'], fg=C['lt'],
            font=('Segoe UI', 10, 'bold'), relief='flat', bd=0,
            padx=14, pady=7, cursor='hand2',
            activebackground=C['success'], activeforeground=C['lt'],
        ).pack(fill='x', ipady=5)
        return f

    # ── Actions ────────────────────────────────────────────────────────────────

    def _do_login(self):
        u = self.lu.get().strip()
        p = self.lp.get()
        if not u or not p:
            messagebox.showerror('Error', 'Fill in username and password.')
            return
        row = get_user_by_credentials(u, p)
        if row:
            self.master.after_login(row['id'], row['username'])
        else:
            messagebox.showerror('Login Failed', 'Incorrect username or password.')

    def _do_reg(self):
        u = self.ru.get().strip()
        p = self.rp.get()
        # Treat placeholder text as empty
        if u == 'min 3 characters':
            u = ''
        if p == 'min 4 characters':
            p = ''
        if not u or not p:
            messagebox.showerror('Error', 'Fill in all fields.')
            return
        if len(u) < 3:
            messagebox.showerror('Error', 'Username must be ≥ 3 characters.')
            return
        if len(p) < 4:
            messagebox.showerror('Error', 'Password must be ≥ 4 characters.')
            return
        try:
            create_user(u, p)
            messagebox.showinfo('Success', 'Account created! You can now log in.')
            self._tab('login')
        except Exception:
            messagebox.showerror('Error', 'Username already taken.')