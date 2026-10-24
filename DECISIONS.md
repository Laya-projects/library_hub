# DECISIONS.md

Decision log for LibraryHub Mini. Each entry gives the problem, the options, the choice and the reason. 

## Phase 1 at a glance

| # | Question | Choice |
|---|---|---|
| D1 | Where do unpaid fines live? | `Fine` records, total calculated when needed |
| D2 | Who works out availability? | `Library.available_copies()` |
| D3 | What does a `Loan` hold? | IDs, not objects |
| D4 | Who writes the error message? | The error class, from raw data |
| D5 | Where does the date and money maths live? | Plain functions in `calculations.py` |
| D6 | How do repositories and the loader work? | `get` returns `None`, loader checks everything first |

## Phase 1: Python + OOP

### D1. Where do unpaid fines live? (R4, R5)
- **Problem:** R4 needs "how much does this member owe?". Karthik owes ₹120 (₹80 + ₹40 unpaid).
- **Options:** A) a stored number on `Member`. B) `Fine` records (`loan_id`, `amount`, `paid`) with the total calculated.
- **Chosen: B.**
- **Why:** a stored number goes stale when a fine is paid. Calculating it keeps one source of truth, and it matches `fines.csv` and the Phase 3 `fines` table.

### D2. Who works out availability?
- **Problem:** how many copies of a title are free? That is `total_copies` minus the open loans (no return date) for that ISBN.
- **Options:** A) `Library` calculates it. B) a repository calculates it (a SQL `COUNT` in Phase 3).
- **Chosen: A.**
- **Why:** simplest for Phase 1, with one source of truth and no stored "available" number. In Phase 3 the method can move behind a repository on purpose.

### D3. Does a `Loan` hold objects or IDs?
- **Problem:** a loan links one member to one item.
- **Options:** A) hold the member and item objects. B) hold `member_id` and `isbn`, and pass the member and item into calculations.
- **Chosen: B.**
- **Why:** IDs match the CSV files and a database row, and a loan can never hold a stale copy of a member. Calculations get what they need, for example `loan.fine(today, member, item)`.

### D4. Who writes the error message?
- **Problem:** the console and the Phase 4 API must show the same `ERROR [code]: message`.
- **Options:** A) the caller passes the finished message. B) the error class receives raw data (names, titles, counts) and builds the message.
- **Chosen: B.**
- **Why:** all wording lives in `errors.py` and is tested in one file, and the data stays available (`error.unpaid`).
- **Details:**
  - `RenewalNotAllowedError` serves R2 and R6, so it has three named constructors: `magazine()`, `limit_reached()` and `someone_waiting()`.
  - `ItemNotAvailableError` uses code `R7`. No sample prints it as an error line, so this is an assumption.
  - Its message is only the first half of the prompt, and the menu adds "Join the waiting list? (y/n)".

### D5. Where does the date and money maths live? (R2, R4, R5, R6, R10)
- **Problem:** `Loan`, `Library` and the tests all need the same maths, and it must exist in one place.
- **Options:** A) plain functions in `calculations.py`. B) methods on `Loan` and `Member`.
- **Chosen: A.**
- **Why:** pure functions take `today` as a parameter, never read the clock, and can be tested with only numbers and dates. `Loan` calls them, so nothing is duplicated.
- **Details:**
  - `days_late` stops counting at the return date, so a returned loan never gets later.
  - `unpaid_total` raises `KeyError` for a fine whose loan is missing, because quietly skipping it could unblock a member. The loader now stops that data earlier (D7).

### D6. How do the repositories and the loader work?
- **Problem:** `Library` must never touch files or dicts, so Phase 3 can swap in a database.
- **Chosen:**
  - `get` returns `None` when nothing is found, and `Library` raises the right error. A repository only stores things. (Rejected: raising inside the repository.)
  - The interfaces use `ABC`, so a missing method is caught at creation. (Rejected: `Protocol`.)
  - A repeated ISBN (R9), member ID, loan ID, or a second fine for one loan raises `ValidationError`. A new `DuplicateISBNError` was rejected as an extra error class.
  - Loans have `update(loan)`: `Library` calls it after every change (return date, renewals, due date). In memory the object is shared so it looks unnecessary, but a database repository only sees a change through this call. A test uses a repository that hands out copies to prove `Library` calls it. Updating an unknown loan raises `LoanNotFoundError`.
  - Collections: a `dict` by ISBN and by member ID, and `list`s for loans and fines. `list_all()` returns a copy of the collection, and the objects inside are shared so `Library` can update them.
  - The loader picks the class with dictionary lookups (no if-chain), requires `YYYY-MM-DD` dates, reads with `utf-8-sig` (Excel's invisible BOM), and names the file and line for a bad row.
  - The loader reads and checks all four files first (unique IDs, every loan and fine points at something real), and only then stores. A broken or missing file raises `ValidationError` and stores nothing.
- **Why:** `Library` stays free of `open()` and `csv`, and bad data never reaches the repositories.
- **Known, for Phase 2:** `InMemoryLoanRepository.get` scans the whole list, so it is O(n). It will be measured in the complexity audit. Reporting line numbers for duplicate IDs is task 2.3.

## Phase 2: DSA

(Entries to be added in Phase 2.)

## Phase 3: Database

(Entries to be added in Phase 3.)

## Phase 4: React

(Entries to be added in Phase 4.)