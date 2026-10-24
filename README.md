# LibraryHub Mini

A small library system for the City Knowledge Library, written in Python with
object-oriented design. It runs as a console menu: list and search the
catalogue, borrow, return, renew, join a waiting list, and see member loans and
an overdue report. Phase 1 of 4 (Python + OOP).

## Run it in 5 minutes

You need **Python 3.10 or newer** and **git**.

### 1. Get the code

```
git clone https://github.com/Laya-projects/library_hub.git
cd library_hub
```

### 2. Create a virtual environment and install

Windows (PowerShell):

```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e . pytest pytest-cov ruff mypy
```

macOS or Linux:

```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e . pytest pytest-cov ruff mypy
```

If PowerShell refuses to activate the environment, run
`Set-ExecutionPolicy -Scope Process RemoteSigned` once and try again.

### 3. Start the program

The sample data is built around the date **2026-10-12**. Set `TODAY` so the
overdue loans and fines come out the same for everyone.

Windows (PowerShell):

```
$env:TODAY="2026-10-12"; python -m libraryhub.main
```

macOS or Linux:

```
TODAY=2026-10-12 python -m libraryhub.main
```

Without `TODAY`, the real date is used. `TODAY` must look like `2026-10-12`.

### 4. Try it

Type a number and press Enter. `0` exits.

```
> 7
Member ID: M002
Loans for Rahul Mehta (Regular: 5 items, 21 days, ₹5/day)
LOAN  TITLE          ISSUED      DUE         STATUS
L001  The Alchemist  2026-09-01  2026-09-22  OVERDUE (20 days)
Active loans: 1 of 5
Unpaid fines: ₹0
> 8
Overdue loans as of 2026-10-12
LOAN  MEMBER       TITLE                DUE         DAYS  FINE SO FAR
L001  Rahul Mehta  The Alchemist        2026-09-22    20  ₹100
L002  Karthik N    Python Crash Course  2026-10-05     7  ₹14
Total overdue: 2   Fines so far: ₹114
```

Handy IDs from the sample data: member `M001` (Asha Raman), book
`9780000000011` (Wings of Fire), loan `L001`, book `9780000000028`
(The Alchemist, all copies out, so borrowing it offers the waiting list).

## The menu

| Choice | What it does |
|--------|--------------|
| 1 | List the catalogue with copies available |
| 2 | Search by title or author (ignores case) |
| 3 | Borrow an item (asks for member ID and ISBN) |
| 4 | Return a loan (asks for loan ID, shows any fine) |
| 5 | Renew a loan |
| 6 | Join the waiting list for a title |
| 7 | Show a member's loans and unpaid fines |
| 8 | Overdue report |
| 0 | Exit |

Money is whole rupees (`₹100`). Dates are `YYYY-MM-DD`. Errors look like
`ERROR [R3]: ...` for a rule violation and `ERROR [ClassName]: ...` otherwise.

## Run the tests

```
python -m pytest
python -m pytest --cov=libraryhub --cov-report=term-missing
python -m ruff check .
python -m mypy src
```

All tests should pass with 100% coverage, and `ruff` and `mypy` should report
no problems.

## Project layout

```
data/                 CSV starter data (books, members, loans)
src/libraryhub/
  items.py            Book, Reference and Magazine (polymorphic items)
  members.py          Student, Regular and other member types
  loans.py            Loan and Fine
  calculations.py     Pure functions: due dates, fines, limits
  errors.py           Every error, with its code and message
  repositories.py     In-memory storage behind interfaces
  csv_loader.py       Reads the CSV files into the repositories
  library.py          The Library service: where the rules are applied
  audit.py            @audit decorator and the audit log
  formatters.py       Turns data into the exact text of the menu
  menu.py             The console menu (no rules inside)
  main.py             Starts everything; reads TODAY
tests/                pytest tests, including a golden session test
DECISIONS.md          Design decisions and why
```

How the layers fit: data and domain classes at the bottom, then pure
calculations, repositories, the `Library` service, formatters, and the menu on
top. The menu never applies a rule itself; it asks `Library` and prints.

## Design decisions

See [DECISIONS.md](DECISIONS.md) for the choices made in this phase and why.

## Rules and tests

The traceability table (rules R1 to R10, the code that enforces each, and the
tests that prove it) is added in step 10.2.