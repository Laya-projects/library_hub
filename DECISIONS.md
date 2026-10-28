# DECISIONS.md

Decision log for LibraryHub Mini. Phase 1 entries give the problem, the options, the choice and the reason. Phase 2 and Phase 3 entries are shorter: what was chosen and why.

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

## Phase 2 at a glance

| # | Question | Choice |
|---|---|---|
| D1 | How are the benchmarks measured? | Median of several runs, setup outside the timer |
| D2 | How is the catalogue sort written? | One `sorted()` with a tuple key |
| D3 | How are repeats and pairs found in one pass? | A dict or set, one lookup per item |
| D4 | What does option 9 print when it undoes a return? | Same shape as the borrow message, plus "fine of ₹X removed" only when a fine existed |
| D5 | Where does the waiting-queue logic live? | A `WaitingQueue` class wrapping a deque |
| D6 | Where does the borrowing history live? | Built on demand from the loans |
| D7 | What does `count_items` return for an unknown category? | `None`, like `path_to` |
| D8 | What does an undo entry store? | IDs and numbers, never the `Loan` object |

## Phase 2: DSA

### D1. Benchmarks
- **What:** the median of several runs (7 by default, 3 for the hand-written sorts, 21 for searches under a millisecond), with the set-up outside the timer.
- **Why:** the median ignores the odd slow run, and building 50,000 books costs far more than the call being measured. Results under 1 ms are noisy: the shape (flat, linear, quadratic) is reliable, the exact ratios are not.

### D2. Catalogue sort
- **What:** one `sorted()` with the key `(top_category(item.category), -item.pages, item.title)`.
- **Why:** one pass and one readable line. Tuples compare field by field, and negating the pages reverses only that field. Rejected: three stable passes (easy to write in the wrong order) and `cmp_to_key` (more code, slower). Negating only works for numbers.

### D3. Repeats, grouping, counting and two-sum
- **What:** a dict or set that remembers what has been seen: a dict from ISBN to its first title, a `defaultdict(list)`, a `Counter`, and a dict from pages to item.
- **Why:** a lookup is O(1) on average, so each task is one pass, O(n), instead of the nested loop's O(n²). Sorting first costs O(n log n) and loses the line numbers and catalogue order.

### D4. Undo-return message
- **What:** `OK: Undid return of 'The Alchemist' by Rahul Mehta (loan L001 is open again, fine of ₹100 removed).` The fine part appears only when a fine was recorded.
- **Why:** the brief gives no sample for it. This has the same shape as the borrow message and names both things that change: the loan reopens and the fine leaves the member's total. The text is built in `format_undone`, so `Library` still prints nothing. Rejected: a fixed "(loan L001 reopened)", which hides the removed fine.

### D5. Waiting queue
- **What:** a `WaitingQueue` class in `dsa/waiting_queue.py` that wraps a `deque`. `Library` calls `join`, `leave`, `place_of` and `rejoin`, and never touches the deque.
- **Why:** the queue's rules (nobody queued twice, places count from 1, rejoin at a place for undo) live in one class that is tested alone. Phase 3 moves the queue to a table, so only this class changes. Rejected: raw deques inside `Library`.

### D6. Borrowing history
- **What:** `Library.borrow_history(member_id)` builds a linked list (`BorrowHistory`) from the member's loans on every call, newest first.
- **Why:** the loans stay the single source of truth, so the history cannot disagree with them, and an undone borrow needs no extra code. The cost is O(L log L) for one member's loans, which is small. Rejected: a stored history per member, which is a second copy to keep in step.

### D7. `count_items` for an unknown category
- **What:** it returns `None`, like `path_to`.
- **Why:** `0` would look like a real answer and hide a typo. `None` forces the caller to handle "no such category", and mypy checks it.

### D8. What an undo entry stores
- **What:** only IDs and numbers: the action, loan ID, member ID, ISBN, the place in the queue and the fine. The stack keeps the last 20 actions, and undoing something that has gone raises a clear error.
- **Why:** a `Loan` is a live object that can change or disappear after it was saved, and the queue place and the fine are not on the loan at all. Rejected: pushing the `Loan` itself, or a snapshot of the whole library.

## Phase 3 at a glance

| # | Question | Choice |
|---|---|---|
| D1 | Is availability stored or calculated? | Calculated: total copies minus open loans, so it cannot drift |
| D2 | What does ON DELETE do for each foreign key? | RESTRICT on all: loans and fines are history and money |
| D3 | How do reference items count in Q11? | Included with their copy count, as in the brief's output |
| D4 | Which Phase 2 structures survive a restart? | Both: waiting list in `reservations`, undo history in its own table |
| D5 | Which database? | SQLite: built in, no install, a fresh database per test |

## Phase 3: SQL

### D1. Availability
- **What:** calculated, not stored: total copies minus the open loans, counted with a `LEFT JOIN`.
- **Why:** the loans are the single source of truth, so the number can never drift. It also matches Phase 1 D2. I would store it only if a measured `EXPLAIN` showed the count was too slow.

### D2. ON DELETE
- **What:** RESTRICT on every foreign key.
- **Why:** loans and fines are history and money. A delete that would orphan them is refused until a person deals with it, so one `DELETE` can never erase them.

### D3. Reference items in Q11
- **What:** included, with their copy count (the Encyclopaedia shows 1 available).
- **Why:** Q11 asks for the copies on the shelf per title, which is a plain count. It also matches the brief's expected output exactly.

### D4. What survives a restart
- **What:** both the waiting list (the `reservations` table) and the undo history (a table of its own).
- **Why:** a restart should not lose a member's place in the queue or the chance to fix the last mistake. Undo entries already hold only IDs and numbers (Phase 2 D8), so they can be stored as rows.

### D5. Database
- **What:** SQLite.
- **Why:** it is built into Python, needs no install, and gives a fresh temporary database for every test, which Part B needs.