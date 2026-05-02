"""page_dashboard.py — Dashboard page: summary cards and charts."""

import datetime
import tkinter as tk

from constants import C, MONTHS
from database import get_allowance, get_monthly_spent, db_get
from widgets import BudgetBar, Tooltip

try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


class DashboardPage(tk.Frame):
    def __init__(self, master, uid: int, uname: str):
        super().__init__(master, bg=C['bg'])
        self.uid   = uid
        self.uname = uname
        t = datetime.date.today()
        self.yr, self.mo = t.year, t.month
        self._build()

    # ── Main layout ───────────────────────────────────────────────────────────

    def _build(self):
        self._build_header()
        self._build_summary_cards()
        self._build_charts()

    def _build_header(self):
        hdr = tk.Frame(self, bg=C['bg'], padx=32, pady=22)
        hdr.pack(fill='x')
        tk.Label(hdr,
                 text=f'Dashboard — {MONTHS[self.mo - 1]} {self.yr}',
                 font=('Segoe UI', 20, 'bold'),
                 bg=C['bg'], fg=C['dk']).pack(side='left')
        tk.Label(hdr,
                 text=f'Welcome back, {self.uname}!',
                 font=('Segoe UI', 12),
                 bg=C['bg'], fg=C['muted']).pack(side='right', pady=6)

    def _build_summary_cards(self):
        alw   = get_allowance(self.uid, self.yr, self.mo)
        spent = get_monthly_spent(self.uid, self.yr, self.mo)
        rem   = alw - spent
        pct   = (spent / alw * 100) if alw > 0 else 0.0
        bar_color = (
            C['success'] if pct < 80
            else C['warning'] if pct < 100
            else C['danger']
        )

        tooltips = {
            'Monthly Allowance': 'Your total budget set for this month.',
            'Total Spent':       'Sum of all expenses recorded this month.',
            'Remaining':         'How much of your allowance is left to spend.',
            'Budget Used':       'Percentage of your monthly allowance already spent.',
        }
        card_defs = [
            ('Monthly Allowance', f'RM{alw:,.2f}',         C['primary'], '💰'),
            ('Total Spent',       f'RM{spent:,.2f}',        C['danger'],  '💸'),
            ('Remaining',         f'RM{max(rem, 0):,.2f}',  C['success'], '✅'),
            ('Budget Used',       f'{pct:.1f}%',            C['warning'], '📊'),
        ]

        cr = tk.Frame(self, bg=C['bg'], padx=32)
        cr.pack(fill='x', pady=(0, 20))

        for i, (lbl, val, col, ico) in enumerate(card_defs):
            card = tk.Frame(cr, bg=C['card'], padx=22, pady=18, relief='flat')
            card.grid(row=0, column=i, padx=(0, 16), sticky='nsew')
            cr.columnconfigure(i, weight=1)

            tk.Frame(card, bg=col, height=4).pack(fill='x', pady=(0, 10))
            tk.Label(card, text=f'{ico}  {lbl}',
                     font=('Segoe UI', 10),
                     bg=C['card'], fg=C['muted']).pack(anchor='w')
            tk.Label(card, text=val,
                     font=('Segoe UI', 22, 'bold'),
                     bg=C['card'], fg=col).pack(anchor='w', pady=(4, 0))

            if lbl == 'Budget Used':
                BudgetBar(card, pct,  C['warning']).pack(fill='x', pady=(6, 0))

            Tooltip(card, tooltips[lbl])

    def _build_charts(self):
        charts = tk.Frame(self, bg=C['bg'], padx=32)
        charts.pack(fill='both', expand=True, pady=(0, 24))
        charts.columnconfigure(0, weight=6)
        charts.columnconfigure(1, weight=4)

        lc = tk.Frame(charts, bg=C['card'], padx=20, pady=16)
        lc.grid(row=0, column=0, sticky='nsew', padx=(0, 16))
        rc = tk.Frame(charts, bg=C['card'], padx=20, pady=16)
        rc.grid(row=0, column=1, sticky='nsew')

        tk.Label(lc, text='Monthly Overview — Last 6 Months',
                 font=('Segoe UI', 13, 'bold'),
                 bg=C['card'], fg=C['dk']).pack(anchor='w', pady=(0, 8))
        tk.Label(rc, text=f'Spending by Category — {MONTHS[self.mo - 1]}',
                 font=('Segoe UI', 13, 'bold'),
                 bg=C['card'], fg=C['dk']).pack(anchor='w', pady=(0, 8))

        if HAS_MPL:
            self._bar_chart(lc)
            self._pie_chart(rc)
        else:
            msg = 'Charts require matplotlib.\nRun: pip install matplotlib'
            for card in (lc, rc):
                tk.Label(card, text=msg, font=('Segoe UI', 12),
                         bg=C['card'], fg=C['muted'], justify='center').pack(expand=True)

    # ── Charts ─────────────────────────────────────────────────────────────────

    def _bar_chart(self, parent):
        today = datetime.date.today()
        data = []
        for i in range(5, -1, -1):
            y, m = today.year, today.month - i
            while m <= 0:
                m += 12
                y -= 1
            data.append((y, m))

        labels = [f"{MONTHS[m - 1][:3]}\n{y}" for y, m in data]
        alws   = [get_allowance(self.uid, y, m)    for y, m in data]
        spents = [get_monthly_spent(self.uid, y, m) for y, m in data]

        fig = Figure(figsize=(9, 3.8), facecolor=C['card'])
        ax  = fig.add_subplot(111, facecolor=C['card'])
        x, w = list(range(len(labels))), 0.35
        ax.bar([i - w / 2 for i in x], alws,   width=w, color='#74b9ff', label='Allowance', zorder=3)
        ax.bar([i + w / 2 for i in x], spents, width=w, color='#fd79a8', label='Spent',     zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=8, color=C['dk'])
        ax.tick_params(axis='y', labelsize=8, colors=C['dk'])
        ax.spines[['top', 'right']].set_visible(False)
        ax.spines[['left', 'bottom']].set_color(C['border'])
        ax.yaxis.grid(True, linestyle='--', alpha=0.5, zorder=0, color=C['border'])
        leg = ax.legend(fontsize=9, facecolor=C['card'], edgecolor=C['border'])
        for txt in leg.get_texts():
            txt.set_color(C['dk'])
        ax.set_ylabel('Amount (RM)', fontsize=9, color=C['dk'])
        fig.tight_layout(pad=1.5)
        FigureCanvasTkAgg(fig, parent).get_tk_widget().pack(fill='both', expand=True)

    def _pie_chart(self, parent):
        rows = db_get(
            "SELECT c.name, COALESCE(SUM(e.amount), 0) AS total "
            "FROM categories c "
            "LEFT JOIN expenses e ON e.category_id = c.id "
            "  AND e.user_id=? AND strftime('%Y-%m', e.expense_date)=? "
            "WHERE c.user_id=? GROUP BY c.id HAVING total > 0",
            (self.uid, f'{self.yr:04d}-{self.mo:02d}', self.uid),
        )
        fig = Figure(figsize=(5, 3.8), facecolor=C['card'])
        ax  = fig.add_subplot(111, facecolor=C['card'])
        if rows:
            colors = ['#74b9ff','#fd79a8','#55efc4','#ffeaa7',
                      '#a29bfe','#fd9644','#26de81','#e17055']
            ax.pie(
                [r['total'] for r in rows],
                labels=[r['name'] for r in rows],
                autopct='%1.1f%%',
                colors=colors[:len(rows)],
                startangle=90,
                textprops={'fontsize': 8, 'color': C['dk']},
            )
        else:
            ax.text(0.5, 0.5, 'No expenses\nthis month',
                    ha='center', va='center', fontsize=12, color=C['muted'],
                    transform=ax.transAxes)
            ax.axis('off')
        fig.tight_layout(pad=1)
        FigureCanvasTkAgg(fig, parent).get_tk_widget().pack(fill='both', expand=True)
