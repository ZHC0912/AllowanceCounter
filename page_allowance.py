"""page_allowance.py — Monthly allowance management page."""

import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from constants import C, MONTHS
from database import db_get, db_one, db_run, get_allowance, get_monthly_spent
from widgets import apply_treeview_style, mbtn, mentry


class AllowancePage(tk.Frame):
    def __init__(self, master, uid: int, uname: str):
        super().__init__(master, bg=C['bg'])
        self.uid = uid
        t = datetime.date.today()
        self.sel_yr = tk.IntVar(value=t.year)
        self.sel_mo = tk.IntVar(value=t.month)
        self._build()
        self._load_current()
        self._load_history()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        tk.Label(self, text='Monthly Allowance',
                 font=('Segoe UI', 20, 'bold'),
                 bg=C['bg'], fg=C['dk']).pack(anchor='w', padx=32, pady=(22, 16))

        body = tk.Frame(self, bg=C['bg'], padx=32)
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)

        self._build_set_panel(body)
        self._build_history_panel(body)

    def _build_set_panel(self, body):
        lc = tk.Frame(body, bg=C['card'], padx=26, pady=24)
        lc.grid(row=0, column=0, sticky='nsew', padx=(0, 16))

        tk.Label(lc, text='Set Allowance',
                 font=('Segoe UI', 14, 'bold'),
                 bg=C['card'], fg=C['dk']).pack(anchor='w', pady=(0, 18))

        def lbl(t):
            tk.Label(lc, text=t, font=('Segoe UI', 10, 'bold'),
                     bg=C['card'], fg=C['dk'], anchor='w').pack(fill='x', pady=(12, 4))

        lbl('Year')
        sp = tk.Spinbox(lc, from_=2000, to=2100, textvariable=self.sel_yr,
                        font=('Segoe UI', 11), command=self._load_current)
        sp.pack(fill='x', ipady=4)
        sp.bind('<Return>', lambda e: self._load_current())

        lbl('Month')
        self._mo_cb = ttk.Combobox(lc, values=MONTHS, state='readonly',
                                   font=('Segoe UI', 11))
        self._mo_cb.current(self.sel_mo.get() - 1)
        self._mo_cb.pack(fill='x', ipady=4)
        self._mo_cb.bind('<<ComboboxSelected>>', lambda e: (
            self.sel_mo.set(MONTHS.index(self._mo_cb.get()) + 1),
            self._load_current(),
        ))

        lbl('Allowance Amount (RM)')
        self._av = tk.StringVar()
        mentry(lc, textvariable=self._av).pack(fill='x', ipady=6)

        tk.Frame(lc, height=18, bg=C['card']).pack()
        mbtn(lc, '💾  Save Allowance', self._save, 'primary').pack(anchor='w')

        self._status = tk.Label(lc, text='', font=('Segoe UI', 10),
                                bg=C['card'], fg=C['success'])
        self._status.pack(anchor='w', pady=(10, 0))

    def _build_history_panel(self, body):
        rc = tk.Frame(body, bg=C['card'], padx=26, pady=24)
        rc.grid(row=0, column=1, sticky='nsew')

        tk.Label(rc, text='Allowance History',
                 font=('Segoe UI', 14, 'bold'),
                 bg=C['card'], fg=C['dk']).pack(anchor='w', pady=(0, 12))

        cols = ('year', 'month', 'allowance', 'spent', 'remaining')
        apply_treeview_style('Alw.Treeview', row_height=32)

        self._ht = ttk.Treeview(rc, columns=cols, show='headings',
                                 style='Alw.Treeview', selectmode='none')
        for col, txt, w in [
            ('year',      'Year',      80),
            ('month',     'Month',     130),
            ('allowance', 'Allowance', 140),
            ('spent',     'Spent',     130),
            ('remaining', 'Remaining', 130),
        ]:
            self._ht.heading(col, text=txt)
            self._ht.column(col, width=w, anchor='center')

        sb = ttk.Scrollbar(rc, orient='vertical', command=self._ht.yview)
        self._ht.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        self._ht.pack(fill='both', expand=True)

    # ── Data helpers ───────────────────────────────────────────────────────────

    def _load_current(self):
        y, m = self.sel_yr.get(), self.sel_mo.get()
        r = db_one('SELECT amount FROM allowances WHERE user_id=? AND year=? AND month=?',
                   (self.uid, y, m))
        self._av.set(f'{r["amount"]:.2f}' if r else '')
        self._status.config(text='')

    def _save(self):
        y, m = self.sel_yr.get(), self.sel_mo.get()
        try:
            amt = float(self._av.get())
            if amt < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror('Error', 'Enter a valid amount (≥ 0).')
            return
        db_run(
            'INSERT INTO allowances (user_id, year, month, amount) VALUES (?, ?, ?, ?) '
            'ON CONFLICT(user_id, year, month) DO UPDATE SET amount = excluded.amount',
            (self.uid, y, m, amt),
        )
        self._status.config(text=f'✓  Saved RM{amt:,.2f} for {MONTHS[m - 1]} {y}')
        self._load_history()

    def _load_history(self):
        for r in self._ht.get_children():
            self._ht.delete(r)
        rows = db_get(
            'SELECT year, month, amount FROM allowances WHERE user_id=? '
            'ORDER BY year DESC, month DESC',
            (self.uid,),
        )
        for i, r in enumerate(rows):
            y, m, alw = r['year'], r['month'], r['amount']
            spent = get_monthly_spent(self.uid, y, m)
            rem   = alw - spent
            row_bg = C['row_alt'] if i % 2 else C['card']
            fg_col = C['danger'] if rem < 0 else C['success']
            tag_id = f'alw_{i}'
            self._ht.insert('', 'end', values=(
                y, MONTHS[m - 1],
                f'RM{alw:,.2f}', f'RM{spent:,.2f}', f'RM{rem:,.2f}',
            ), tags=(tag_id,))
            self._ht.tag_configure(tag_id, background=row_bg, foreground=fg_col)
