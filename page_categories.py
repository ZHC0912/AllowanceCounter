"""page_categories.py — Categories management page."""

import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from constants import C
from database import db_get, db_one, db_run, get_categories
from widgets import BudgetBar, mbtn, mentry


class CategoriesPage(tk.Frame):
    def __init__(self, master, uid: int, uname: str):
        super().__init__(master, bg=C['bg'])
        self.uid = uid
        self._build()
        self._load()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        tk.Label(self, text='Categories',
                 font=('Segoe UI', 20, 'bold'),
                 bg=C['bg'], fg=C['dk']).pack(anchor='w', padx=32, pady=(22, 16))

        body = tk.Frame(self, bg=C['bg'], padx=32)
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        self._build_list_panel(body)
        self._build_add_panel(body)

    def _build_list_panel(self, body):
        lc = tk.Frame(body, bg=C['card'], padx=24, pady=22)
        lc.grid(row=0, column=0, sticky='nsew', padx=(0, 16))

        tk.Label(lc, text='Your Categories',
                 font=('Segoe UI', 13, 'bold'),
                 bg=C['card'], fg=C['dk']).pack(anchor='w', pady=(0, 12))

        lf = tk.Frame(lc, bg=C['card'])
        lf.pack(fill='both', expand=True)
        self._lb = tk.Listbox(
            lf, font=('Segoe UI', 12),
            bg=C['entry_bg'], fg=C['dk'],
            selectbackground=C['primary'], selectforeground='white',
            relief='solid', bd=1, highlightthickness=0, activestyle='none',
        )
        sb = ttk.Scrollbar(lf, orient='vertical', command=self._lb.yview)
        self._lb.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        self._lb.pack(fill='both', expand=True)

        btn_row = tk.Frame(lc, bg=C['card'])
        btn_row.pack(fill='x', pady=(14, 0))
        mbtn(btn_row, '  Edit  ', self._edit_category, 'ghost').pack(side='left', padx=(0, 8))
        mbtn(btn_row, '  Delete  ', self._delete, 'danger').pack(side='left')

    def _build_add_panel(self, body):
        rc = tk.Frame(body, bg=C['card'], padx=24, pady=22)
        rc.grid(row=0, column=1, sticky='nsew')

        tk.Label(rc, text='Add New Category',
                 font=('Segoe UI', 13, 'bold'),
                 bg=C['card'], fg=C['dk']).pack(anchor='w', pady=(0, 12))

        tk.Label(rc, text='Category Name',
                 font=('Segoe UI', 10, 'bold'),
                 bg=C['card'], fg=C['dk'], anchor='w').pack(fill='x', pady=(0, 4))
        self._nv = tk.StringVar()
        mentry(rc, textvariable=self._nv, width=26).pack(fill='x', ipady=6)

        tk.Label(rc, text='Budget Cap (RM / month, optional)',
                 font=('Segoe UI', 10, 'bold'),
                 bg=C['card'], fg=C['dk'], anchor='w').pack(fill='x', pady=(10, 4))
        self._bv = tk.StringVar()
        mentry(rc, textvariable=self._bv, width=26).pack(fill='x', ipady=6)

        tk.Frame(rc, height=14, bg=C['card']).pack()
        mbtn(rc, '＋  Add Category', self._add, 'success').pack(anchor='w')
        tk.Frame(rc, height=20, bg=C['card']).pack()

        tk.Label(rc, text='Budget Usage This Month',
                 font=('Segoe UI', 12, 'bold'),
                 bg=C['card'], fg=C['dk']).pack(anchor='w', pady=(0, 8))
        self._budget_frame = tk.Frame(rc, bg=C['card'])
        self._budget_frame.pack(fill='x')

    # ── Data loaders ───────────────────────────────────────────────────────────

    def _load(self):
        self._lb.delete(0, 'end')
        self._cats = get_categories(self.uid)
        self._ids  = []
        for i, r in enumerate(self._cats):
            cap_str = f'  (cap: RM{r["budget_cap"]:,.0f})' if r['budget_cap'] else ''
            self._lb.insert('end', f'  {r["name"]}{cap_str}')
            self._ids.append(r['id'])
            # Alternating stripe colors
            if i % 2 == 0:
                self._lb.itemconfig(i, background=C['card'], foreground=C['dk'])
            else:
                self._lb.itemconfig(i, background=C['row_alt'], foreground=C['dk'])
        self._load_budget_usage()

    def _load_budget_usage(self):
        for w in self._budget_frame.winfo_children():
            w.destroy()

        today = datetime.date.today()
        ym    = f'{today.year:04d}-{today.month:02d}'
        cats  = db_get(
            'SELECT id, name, budget_cap FROM categories '
            'WHERE user_id=? AND budget_cap IS NOT NULL ORDER BY name',
            (self.uid,),
        )
        if not cats:
            tk.Label(self._budget_frame, text='No budget caps set yet.',
                     font=('Segoe UI', 10), bg=C['card'], fg=C['muted']).pack(anchor='w')
            return

        for r in cats:
            spent_row = db_one(
                "SELECT COALESCE(SUM(amount), 0) AS s FROM expenses "
                "WHERE user_id=? AND category_id=? AND strftime('%Y-%m', expense_date)=?",
                (self.uid, r['id'], ym),
            )
            spent = spent_row['s'] if spent_row else 0
            cap   = r['budget_cap']
            pct   = min(spent / cap * 100, 100) if cap else 0
            col   = C['success'] if pct < 80 else (C['warning'] if pct < 100 else C['danger'])

            row_f = tk.Frame(self._budget_frame, bg=C['card'])
            row_f.pack(fill='x', pady=(0, 10))
            tk.Label(row_f, text=r['name'],
                     font=('Segoe UI', 10, 'bold'),
                     bg=C['card'], fg=C['dk']).pack(anchor='w')
            info_row = tk.Frame(row_f, bg=C['card'])
            info_row.pack(fill='x')
            tk.Label(info_row, text=f'RM{spent:,.2f} / RM{cap:,.2f}',
                     font=('Segoe UI', 9), bg=C['card'], fg=C['muted']).pack(side='left')
            tk.Label(info_row, text=f'{pct:.0f}%',
                     font=('Segoe UI', 9, 'bold'), bg=C['card'], fg=col).pack(side='right')
            BudgetBar(row_f, pct, col).pack(fill='x')

    # ── Actions ────────────────────────────────────────────────────────────────

    def _edit_category(self):
        sel = self._lb.curselection()
        if not sel:
            messagebox.showinfo('Select', 'Select a category to edit.')
            return
        idx    = sel[0]
        cat_id = self._ids[idx]
        cat    = self._cats[idx]

        d = tk.Toplevel(self)
        d.title('Edit Category')
        d.configure(bg=C['bg'])
        d.resizable(False, False)
        w, h = 360, 280
        sw, sh = d.winfo_screenwidth(), d.winfo_screenheight()
        d.geometry(f'{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}')
        d.grab_set()

        pad = tk.Frame(d, bg=C['bg'], padx=28, pady=24)
        pad.pack(fill='both', expand=True)
        tk.Label(pad, text=f'Edit "{cat["name"]}"',
                 font=('Segoe UI', 13, 'bold'),
                 bg=C['bg'], fg=C['dk']).pack(anchor='w', pady=(0, 14))

        # Name field
        tk.Label(pad, text='Category Name',
                 font=('Segoe UI', 10), bg=C['bg'], fg=C['muted']).pack(anchor='w')
        name_entry = mentry(pad)
        name_entry.pack(fill='x', ipady=5, pady=(4, 12))
        name_entry.delete(0, 'end')
        name_entry.insert(0, cat['name'])

        # Budget field
        tk.Label(pad, text='Monthly Cap (RM — leave blank to remove)',
                 font=('Segoe UI', 10), bg=C['bg'], fg=C['muted']).pack(anchor='w')
        budget_entry = mentry(pad)
        budget_entry.pack(fill='x', ipady=5, pady=(4, 16))
        if cat['budget_cap']:
            budget_entry.insert(0, str(cat['budget_cap']))

        def save():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showerror('Error', 'Category name cannot be empty.', parent=d)
                return

            val = budget_entry.get().strip()
            cap = None
            if val:
                try:
                    cap = float(val)
                    if cap < 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror('Error', 'Enter a valid amount or leave blank.', parent=d)
                    return

            try:
                db_run('UPDATE categories SET name=?, budget_cap=? WHERE id=?',
                       (new_name, cap, cat_id))
            except Exception:
                messagebox.showerror('Error', 'That category name is already taken.', parent=d)
                return

            d.destroy()
            self._load()

        bf = tk.Frame(pad, bg=C['bg'])
        bf.pack(fill='x')
        mbtn(bf, 'Cancel', d.destroy, 'ghost').pack(side='right', padx=(8, 0))
        mbtn(bf, 'Save',   save,      'primary').pack(side='right')

    def _add(self):
        name = self._nv.get().strip()
        if not name:
            messagebox.showerror('Error', 'Enter a category name.')
            return
        cap_str = self._bv.get().strip()
        cap = None
        if cap_str:
            try:
                cap = float(cap_str)
                if cap < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror('Error', 'Budget cap must be a positive number.')
                return
        try:
            db_run('INSERT INTO categories (user_id, name, budget_cap) VALUES (?, ?, ?)',
                   (self.uid, name, cap))
            self._nv.set('')
            self._bv.set('')
            self._load()
        except Exception:
            messagebox.showerror('Error', 'Category already exists.')

    def _delete(self):
        sel = self._lb.curselection()
        if not sel:
            messagebox.showinfo('Select', 'Select a category to delete.')
            return
        idx    = sel[0]
        cat_id = self._ids[idx]
        raw    = self._lb.get(idx).strip()
        name   = raw.split('  (cap:')[0].strip()

        cnt = db_one('SELECT COUNT(*) AS c FROM expenses WHERE category_id=?', (cat_id,))
        if cnt and cnt['c'] > 0:
            messagebox.showerror(
                'Cannot Delete',
                f'"{name}" has {cnt["c"]} linked expense(s).\nDelete those expenses first.',
            )
            return
        if messagebox.askyesno('Confirm', f'Delete category "{name}"?'):
            db_run('DELETE FROM categories WHERE id=?', (cat_id,))
            self._load()