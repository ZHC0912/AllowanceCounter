"""page_expenses.py — Expenses list page and Add/Edit expense dialog."""

import csv
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from constants import C, MONTHS, is_dark
from database import db_get, db_one, db_run, get_categories
from widgets import apply_treeview_style, mbtn, mentry, Toast

try:
    from tkcalendar import DateEntry
    HAS_CAL = True
except ImportError:
    HAS_CAL = False


# ── Expenses Page ──────────────────────────────────────────────────────────────

class ExpensesPage(tk.Frame):
    def __init__(self, master, uid: int, uname: str):
        super().__init__(master, bg=C['bg'])
        self.uid   = uid
        self.uname = uname
        t = datetime.date.today()
        self.sel_yr  = tk.IntVar(value=t.year)
        self.sel_mo  = tk.IntVar(value=t.month)
        self._sort_col = 'date'
        self._sort_rev = True
        self._build()
        self._load()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        self._build_header()
        self._build_search_bar()
        self._build_table()
        self._build_action_bar()

    def _build_header(self):
        hdr = tk.Frame(self, bg=C['bg'], padx=32, pady=20)
        hdr.pack(fill='x')
        tk.Label(hdr, text='Expenses',
                 font=('Segoe UI', 20, 'bold'),
                 bg=C['bg'], fg=C['dk']).pack(side='left')

        rhs = tk.Frame(hdr, bg=C['bg'])
        rhs.pack(side='right')

        mbtn(rhs, '📤  Export CSV', self._export_csv, 'ghost').pack(side='left', padx=(0, 8))
        mbtn(rhs, '＋  Add Expense', self._open_add, 'primary').pack(side='left')

    def _build_search_bar(self):
        sf = tk.Frame(self, bg=C['bg'], padx=32)
        sf.pack(fill='x', pady=(0, 8))
        tk.Label(sf, text='🔍', font=('Segoe UI', 13),
                 bg=C['bg'], fg=C['muted']).pack(side='left')
        self._search_var = tk.StringVar()
        self._search_var.trace_add('write', lambda *a: self._load())
        mentry(sf, textvariable=self._search_var, width=30).pack(
            side='left', padx=(6, 16), ipady=4)

        tk.Label(sf, text='Category:', font=('Segoe UI', 10),
                 bg=C['bg'], fg=C['muted']).pack(side='left', padx=(0, 4))
        self._cat_filter = tk.StringVar(value='All')
        self._cat_cb = ttk.Combobox(sf, textvariable=self._cat_filter,
                                    state='readonly', width=16, font=('Segoe UI', 10))
        self._cat_cb.pack(side='left')
        self._cat_cb.bind('<<ComboboxSelected>>', lambda e: self._load())
        self._refresh_cat_filter()

        # ── Month & Year ──────────────────────────────────────────────────────
        tk.Label(sf, text='Month:', font=('Segoe UI', 10),
                 bg=C['bg'], fg=C['muted']).pack(side='left', padx=(16, 4))
        self._mo_cb = ttk.Combobox(sf, values=MONTHS, width=11, state='readonly',
                                   font=('Segoe UI', 10))
        self._mo_cb.current(self.sel_mo.get() - 1)
        self._mo_cb.pack(side='left', padx=(0, 10))
        self._mo_cb.bind('<<ComboboxSelected>>', lambda e: (
            self.sel_mo.set(MONTHS.index(self._mo_cb.get()) + 1), self._load()))

        tk.Label(sf, text='Year:', font=('Segoe UI', 10),
                 bg=C['bg'], fg=C['muted']).pack(side='left', padx=(0, 4))
        sp = tk.Spinbox(sf, from_=2000, to=2100, textvariable=self.sel_yr,
                        width=6, font=('Segoe UI', 10), command=self._load)
        sp.pack(side='left')
        sp.bind('<Return>', lambda e: self._load())

    def _build_table(self):
        tf = tk.Frame(self, bg=C['bg'], padx=32)
        tf.pack(fill='both', expand=True)

        rec_even_bg = '#1a3a2e' if is_dark() else '#e8f8f0'
        rec_odd_bg  = '#1f4535' if is_dark() else '#d5f5e3'
        rec_fg      = '#55efc4' if is_dark() else '#00b894'

        apply_treeview_style('Exp.Treeview', row_height=36)

        wrap = tk.Frame(tf, bg=C['card'])
        wrap.pack(fill='both', expand=True)

        col_defs = [
            ('date',        'Date',        140, 'center'),
            ('category',    'Category',    180, 'center'),
            ('amount',      'Amount',      130, 'e'),
            ('description', 'Description', 480, 'w'),
            ('recurring',   '🔄',           60, 'center'),
        ]
        self.tree = ttk.Treeview(wrap, columns=[c for c, *_ in col_defs],
                                  show='headings', style='Exp.Treeview',
                                  selectmode='browse')
        for col, txt, w, anc in col_defs:
            self.tree.heading(col, text=txt, command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=w, anchor=anc)

        self.tree.tag_configure('even',           background=C['card'],    foreground=C['dk'])
        self.tree.tag_configure('odd',            background=C['row_alt'], foreground=C['dk'])
        self.tree.tag_configure('recurring_even', background=rec_even_bg,  foreground=rec_fg)
        self.tree.tag_configure('recurring_odd',  background=rec_odd_bg,   foreground=rec_fg)

        sb = ttk.Scrollbar(wrap, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<Double-1>', lambda e: self._edit_selected())

    def _build_action_bar(self):
        ab = tk.Frame(self, bg=C['bg'], padx=32, pady=14)
        ab.pack(fill='x')
        self._total_lbl = tk.Label(ab, text='Total: RM0.00',
                                   font=('Segoe UI', 13, 'bold'),
                                   bg=C['bg'], fg=C['dk'])
        self._total_lbl.pack(side='left')
        mbtn(ab, '  Delete  ', self._delete_selected, 'danger').pack(side='right', padx=(8, 0))
        mbtn(ab, '  Edit  ',   self._edit_selected,   'ghost').pack(side='right')

    # ── Data helpers ───────────────────────────────────────────────────────────

    def _refresh_cat_filter(self):
        cats  = get_categories(self.uid)
        names = ['All'] + [r['name'] for r in cats]
        self._cat_cb['values'] = names
        if self._cat_filter.get() not in names:
            self._cat_filter.set('All')

    def _sort_by(self, col: str):
        if self._sort_col == col:
            self._sort_rev = not self._sort_rev
        else:
            self._sort_col = col
            self._sort_rev = False
        self._load()

    def _load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        y, m       = self.sel_yr.get(), self.sel_mo.get()
        search     = self._search_var.get().strip().lower()
        cat_filter = self._cat_filter.get()

        rows = db_get(
            "SELECT e.id, e.expense_date, c.name AS cat, e.amount, e.description, e.is_recurring "
            "FROM expenses e JOIN categories c ON c.id = e.category_id "
            "WHERE e.user_id=? AND strftime('%Y-%m', e.expense_date)=? "
            "ORDER BY e.expense_date DESC, e.created_at DESC",
            (self.uid, f'{y:04d}-{m:02d}'),
        )
        if search:
            rows = [r for r in rows
                    if search in (r['description'] or '').lower()
                    or search in r['cat'].lower()]
        if cat_filter != 'All':
            rows = [r for r in rows if r['cat'] == cat_filter]

        sort_key = {
            'date':        lambda r: r['expense_date'],
            'category':    lambda r: r['cat'],
            'amount':      lambda r: r['amount'],
            'description': lambda r: (r['description'] or '').lower(),
            'recurring':   lambda r: r['is_recurring'],
        }
        if self._sort_col in sort_key:
            rows = sorted(rows, key=sort_key[self._sort_col], reverse=self._sort_rev)

        total = 0.0
        for i, r in enumerate(rows):
            is_rec = bool(r['is_recurring'])
            tag = (('recurring_' if is_rec else '') + ('even' if i % 2 == 0 else 'odd'))
            self.tree.insert('', 'end', iid=str(r['id']),
                             values=(r['expense_date'], r['cat'],
                                     f'RM{r["amount"]:,.2f}',
                                     r['description'] or '',
                                     '🔄' if is_rec else ''),
                             tags=(tag,))
            total += r['amount']
        self._total_lbl.config(text=f'Total: RM{total:,.2f}')

    # ── Actions ────────────────────────────────────────────────────────────────

    def _export_csv(self):
        y, m = self.sel_yr.get(), self.sel_mo.get()
        path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv'), ('All files', '*.*')],
            initialfile=f'expenses_{y}_{m:02d}.csv',
            title='Export Expenses to CSV',
        )
        if not path:
            return
        rows = db_get(
            "SELECT e.expense_date, c.name AS cat, e.amount, e.description, e.is_recurring "
            "FROM expenses e JOIN categories c ON c.id = e.category_id "
            "WHERE e.user_id=? AND strftime('%Y-%m', e.expense_date)=? "
            "ORDER BY e.expense_date DESC",
            (self.uid, f'{y:04d}-{m:02d}'),
        )
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['Date', 'Category', 'Amount', 'Description', 'Recurring'])
                for r in rows:
                    w.writerow([r['expense_date'], r['cat'], r['amount'],
                                r['description'] or '',
                                'Yes' if r['is_recurring'] else 'No'])
            Toast.show(self.winfo_toplevel(), f'✓  Exported {len(rows)} rows to CSV')
        except Exception as ex:
            messagebox.showerror('Export Error', str(ex))

    def _open_add(self):
        d = ExpenseDialog(self, self.uid)
        self.wait_window(d)
        self._refresh_cat_filter()
        self._load()

    def _edit_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo('Select Row', 'Select an expense to edit.')
            return
        row = db_one('SELECT * FROM expenses WHERE id=?', (int(sel[0]),))
        if row:
            d = ExpenseDialog(self, self.uid, expense=row)
            self.wait_window(d)
            self._load()

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo('Select Row', 'Select an expense to delete.')
            return
        eid = int(sel[0])
        row = db_one('SELECT * FROM expenses WHERE id=?', (eid,))
        if not row:
            return
        if not messagebox.askyesno('Confirm Delete', 'Delete this expense record?'):
            return
        db_run('DELETE FROM expenses WHERE id=?', (eid,))
        self._load()

        saved = dict(row)

        def undo():
            db_run(
                'INSERT INTO expenses '
                '(user_id, category_id, amount, description, expense_date, is_recurring) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (saved['user_id'], saved['category_id'], saved['amount'],
                 saved['description'], saved['expense_date'], saved['is_recurring']),
            )
            self._load()

        Toast.show(self.winfo_toplevel(),
                   f'Deleted: RM{row["amount"]:,.2f}', undo_cb=undo)


# ── Expense Dialog (Add / Edit) ────────────────────────────────────────────────

class ExpenseDialog(tk.Toplevel):
    def __init__(self, master, uid: int, expense=None):
        super().__init__(master)
        self.uid     = uid
        self.expense = expense
        self.title('Edit Expense' if expense else 'Add Expense')
        self.configure(bg=C['bg'])
        self.resizable(False, False)
        w, h = 520, 520
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f'{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}')
        self.grab_set()
        self.focus_force()
        self._build()
        if expense:
            self._populate()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        pad = tk.Frame(self, bg=C['bg'], padx=36, pady=28)
        pad.pack(fill='both', expand=True)

        tk.Label(pad,
                 text='Edit Expense' if self.expense else 'Add New Expense',
                 font=('Segoe UI', 16, 'bold'),
                 bg=C['bg'], fg=C['dk']).pack(anchor='w', pady=(0, 18))

        def lbl(t):
            tk.Label(pad, text=t, font=('Segoe UI', 10, 'bold'),
                     bg=C['bg'], fg=C['dk'], anchor='w').pack(fill='x', pady=(10, 3))

        # Date
        lbl('Date')
        today = datetime.date.today()
        if HAS_CAL:
            self._date_entry = DateEntry(pad, date_pattern='yyyy-mm-dd',
                                         font=('Segoe UI', 11))
            self._date_entry.pack(fill='x', ipady=4)
        else:
            dr = tk.Frame(pad, bg=C['bg'])
            dr.pack(fill='x')
            years = [str(y) for y in range(today.year - 5, today.year + 2)]
            self.yv = tk.StringVar(value=str(today.year))
            self.mv = tk.StringVar(value=MONTHS[today.month - 1])
            self.dv = tk.StringVar(value=str(today.day))
            ttk.Combobox(dr, textvariable=self.yv, values=years,
                         width=7, state='readonly').pack(side='left', padx=(0, 6))
            ttk.Combobox(dr, textvariable=self.mv, values=MONTHS,
                         width=12, state='readonly').pack(side='left', padx=(0, 6))
            ttk.Combobox(dr, textvariable=self.dv,
                         values=[str(d) for d in range(1, 32)],
                         width=5, state='readonly').pack(side='left')
            tk.Label(pad, text='Tip: pip install tkcalendar for a calendar picker',
                     font=('Segoe UI', 8), bg=C['bg'], fg=C['muted']).pack(anchor='w')

        # Category
        lbl('Category')
        cats = db_get('SELECT id, name FROM categories WHERE user_id=? ORDER BY name', (self.uid,))
        self._cnames = [r['name'] for r in cats]
        self._cids   = [r['id']   for r in cats]
        self.cv = tk.StringVar(value=self._cnames[0] if self._cnames else '')
        ttk.Combobox(pad, textvariable=self.cv, values=self._cnames,
                     state='readonly', width=28).pack(fill='x', ipady=4)

        # Amount
        lbl('Amount (RM)')
        self.av = tk.StringVar()
        mentry(pad, textvariable=self.av).pack(fill='x', ipady=5)

        # Description
        lbl('Description (optional)')
        self.descv = tk.StringVar()
        mentry(pad, textvariable=self.descv).pack(fill='x', ipady=5)

        # Recurring
        rec_row = tk.Frame(pad, bg=C['bg'])
        rec_row.pack(fill='x', pady=(14, 0))
        self.rec_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            rec_row, text='🔄  Recurring monthly expense',
            variable=self.rec_var,
            font=('Segoe UI', 11), bg=C['bg'], fg=C['dk'],
            activebackground=C['bg'], selectcolor=C['card'],
            relief='flat',
        ).pack(anchor='w')
        tk.Label(rec_row, text='Auto-added every month until deleted',
                 font=('Segoe UI', 9), bg=C['bg'], fg=C['muted']).pack(anchor='w', padx=(24, 0))

        # Buttons
        bf = tk.Frame(pad, bg=C['bg'])
        bf.pack(fill='x', pady=(20, 0))
        mbtn(bf, 'Cancel', self.destroy, 'ghost').pack(side='right', padx=(8, 0))
        mbtn(bf, 'Save',   self._save,   'primary').pack(side='right')

    # ── Data helpers ───────────────────────────────────────────────────────────

    def _get_date_str(self):
        if HAS_CAL:
            return self._date_entry.get_date().isoformat()
        try:
            y = int(self.yv.get())
            m = MONTHS.index(self.mv.get()) + 1
            d = int(self.dv.get())
            return datetime.date(y, m, d).isoformat()
        except Exception:
            return None

    def _populate(self):
        e = self.expense
        d = datetime.date.fromisoformat(e['expense_date'])
        if HAS_CAL:
            self._date_entry.set_date(d)
        else:
            self.yv.set(str(d.year))
            self.mv.set(MONTHS[d.month - 1])
            self.dv.set(str(d.day))
        self.av.set(str(e['amount']))
        self.descv.set(e['description'] or '')
        self.rec_var.set(bool(e['is_recurring']))
        cat = db_one('SELECT name FROM categories WHERE id=?', (e['category_id'],))
        if cat and cat['name'] in self._cnames:
            self.cv.set(cat['name'])

    # ── Save ───────────────────────────────────────────────────────────────────

    def _save(self):
        if not self.cv.get():
            messagebox.showerror('Error', 'Select a category.', parent=self)
            return
        try:
            amt = float(self.av.get())
            if amt <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror('Error', 'Enter a valid positive amount.', parent=self)
            return

        date_str = self._get_date_str()
        if not date_str:
            messagebox.showerror('Error', 'Invalid date.', parent=self)
            return

        cat_id = next(
            (self._cids[i] for i, n in enumerate(self._cnames) if n == self.cv.get()),
            None,
        )
        if cat_id is None:
            messagebox.showerror('Error', 'Category not found.', parent=self)
            return

        desc   = self.descv.get().strip()
        is_rec = int(self.rec_var.get())

        if self.expense:
            db_run(
                'UPDATE expenses SET category_id=?, amount=?, description=?, '
                'expense_date=?, is_recurring=? WHERE id=?',
                (cat_id, amt, desc, date_str, is_rec, self.expense['id']),
            )
        else:
            db_run(
                'INSERT INTO expenses '
                '(user_id, category_id, amount, description, expense_date, is_recurring) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (self.uid, cat_id, amt, desc, date_str, is_rec),
            )
        self.destroy()