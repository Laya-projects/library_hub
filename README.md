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

The program works like a librarian's desk: type a number, answer a few
questions, and it replies. Data is held in memory and reloaded from the CSV
files on every start, so nothing is saved when you exit.

| Choice | What it does | What you type | Example result |
|--------|--------------|---------------|----------------|
| 1 | List the catalogue | nothing | A table. `2 of 2` means both copies are free, `0 of 1` means the only copy is out, `not borrowable` is a reference item. |
| 2 | Search by title or author (ignores case) | a word, e.g. `paulo` | `1 result:` and the matching items, or `No items match 'zzz'.` |
| 3 | Borrow | member ID, then ISBN | `OK: Asha Raman borrowed 'Wings of Fire'. Due 2026-10-26.` If every copy is out it asks `Join the waiting list? (y/n)`. `y` joins the queue, anything else skips. |
| 4 | Return | loan ID | `OK: Rahul Mehta returned 'The Alchemist'. Late by 20 days. Fine: ₹100.` Adds `Next on waiting list: <name>.` when someone is waiting. |
| 5 | Renew | loan ID | `OK: Renewed 'Sapiens' (renewal 1 of 2). New due date …` Refused for magazines, at the renewal limit, or when someone is waiting. |
| 6 | Join the waiting list | member ID, then ISBN | `OK: Asha Raman is #1 on the waiting list for 'The Alchemist'.` The number is the place in the queue. |
| 7 | Member loans | member ID | The member's current loans, `OVERDUE (20 days)` when late, how many items they hold out of their limit, and their unpaid fines. |
| 8 | Overdue report | nothing | Every late loan, longest overdue first. `DAYS` is days late, `FINE SO FAR` is what they would owe if returned today, with totals at the end. |
| 0 | Exit | nothing | Quits the program. |

Money is whole rupees (`₹100`). Dates are `YYYY-MM-DD`. Errors look like
`ERROR [R3]: ...` for a rule violation and `ERROR [ClassName]: ...` otherwise.

**Why the dates are fixed:** `TODAY=2026-10-12` makes the program pretend that
is today, so everyone sees the same overdue loans and fines.

**Try a short story** (borrow, waiting list, return):

1. `3`, `M001`, `9780000000028`: no copies are free, so it asks about the
   waiting list. Answer `y`.
2. `4`, `L001`: the copy comes back, and the output ends with
   `Next on waiting list: Asha Raman.`

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
## Rules and tests

| Rule | What it says | Enforced in | Tests |
|------|--------------|-------------|-------|
| R1 | Reference items can never be borrowed | `Library._check_borrowable`, `ItemNotBorrowableError` | TODO |
| R2 | Magazines get 7 days and cannot be renewed | `Library.renew` (via `item.max_renewals()`), `calculations.due_date` | TODO |
| R3 | Each membership has an item limit | `Library._check_limit`, `Member.borrow_limit` | TODO |
| R4 | Borrowing is blocked when unpaid fines are above ₹100 | `Library._check_fines`, `calculations.exceeds_fine_limit` | TODO |
| R5 | A fine is capped at the item's price | `Loan.fine` / `calculations` | TODO |
| R6 | Renewals are limited, and not allowed while someone waits | `Library.renew`, `RenewalNotAllowedError` | TODO |
| R7 | No free copy: offer the waiting list, first come first served | `Library._check_available`, `Library.reserve`, `Library._place_in_line` | TODO |
| R8 | A member cannot hold two copies of the same title | `Library._check_no_duplicate`, `DuplicateLoanError` | TODO |
| R9 | An ISBN is exactly 13 digits | `items.validate_isbn`, `InvalidISBNError` | TODO |
| R10 | Returning on the due date is not late | `Loan.days_late` | TODO |