# Allowance Counter — Project Structure

```
allowance_counter/
│
├── main.py               # Entry point — App(tk.Tk) root window, page transitions
├── constants.py          # Theme dicts (LIGHT/DARK), active theme dict C, set_theme()
├── database.py           # All SQLite helpers: init_db, CRUD wrappers, business queries
├── widgets.py            # Reusable UI components: mbtn, mentry, Toast, Tooltip, BudgetBar
├── shell.py              # MainShell: sidebar nav + lazy page router
│
├── page_login.py         # Login & Register screen
├── page_dashboard.py     # Dashboard: summary cards + matplotlib charts
├── page_expenses.py      # Expenses list page + ExpenseDialog (Add/Edit)
├── page_categories.py    # Category management + budget usage bars
├── page_allowance.py     # Set monthly allowance + history table
└── page_settings.py      # Profile / change password / danger zone
```

## Dependency graph

```
main.py
  ├── constants.py        (no local imports)
  ├── database.py         ← constants
  ├── widgets.py          ← constants
  ├── page_login.py       ← constants, database, widgets
  └── shell.py            ← constants
        └── page_*.py     ← constants, database, widgets  (lazy-imported)
```

## Running

```bash
pip install matplotlib tkcalendar   # optional but recommended
python main.py
```

## Adding a new page

1. Create `page_mypage.py` with a `MyPage(tk.Frame)` class.
2. Add a nav entry in `shell.py` → `_build_sidebar()` nav_items list.
3. Add the `pid → class` mapping in `shell.py` → `_get_page_class()`.
