# DECISIONS.md

Decision log for LibraryHub Mini. Each phase starts with a table of its decisions, followed by the decisions themselves: **what** was chosen and **why**. Numbering restarts in every phase, so a reference such as "Phase 2 D8" names the phase.

---

## Phase 1: Python and OOP

| # | Question | Choice |
|---|---|---|
| D1 | Where do unpaid fines live? | `Fine` records; the total is calculated when needed |
| D2 | Who works out availability? | `Library.available_copies()` |
| D3 | What does a `Loan` hold? | IDs, not objects |
| D4 | Who writes the error message? | The error class, from raw data |
| D5 | Where does the date and money maths live? | Plain functions in `calculations.py` |
| D6 | How do repositories and the loader work? | `get` returns `None`; the loader checks everything first |

### D1. Unpaid fines (R4, R5)
- **What:** `Fine` records (`loan_id`, `amount`, `paid`), with the total calculated when needed.
- **Why:** a stored number on `Member` goes stale when a fine is paid. Calculating it keeps one source of truth, and it matches `fines.csv` and the Phase 3 `fines` table.

### D2. Availability
- **What:** `Library.available_copies()` returns `total_copies` minus the open loans (no return date) for that ISBN.
- **Why:** simplest for Phase 1, with no stored "available" number to drift. In Phase 3 the method can move behind a repository on purpose.

### D3. What a `Loan` holds
- **What:** `member_id` and `isbn`, not the member and item objects. Calculations receive the member and item, for example `loan.fine(today, member, item)`.
- **Why:** IDs match the CSV files and a database row, and a loan can never hold a stale copy of a member.

### D4. Error messages
- **What:** the error class receives raw data (names, titles, counts) and builds the message itself. `RenewalNotAllowedError` serves R2 and R6 through three constructors: `magazine()`, `limit_reached()` and `someone_waiting()`.
- **Why:** all wording lives in `errors.py`, so the console and the Phase 4 API show the same `ERROR [code]: message`, and the data stays available (`error.unpaid`). Assumption: `ItemNotAvailableError` uses code `R7`, because no sample prints it as an error line.

### D5. Date and money maths (R2, R4, R5, R6, R10)
- **What:** pure functions in `calculations.py` that take `today` as a parameter and never read the clock. `Loan` calls them.
- **Why:** they can be tested with only numbers and dates, and nothing is duplicated. `unpaid_total` raises `KeyError` for a fine whose loan is missing, because quietly skipping it could unblock a member.

### D6. Repositories and the loader
- **What:** `get` returns `None` when nothing is found and `Library` raises the right error. The interfaces use `ABC`. Repeated IDs raise `ValidationError`. Loans have `update(loan)`, which `Library` calls after every change. The loader reads and checks all four files first, and only then stores.
- **Why:** `Library` stays free of `open()` and `csv`, a database repository only sees a change through `update`, and bad data never reaches the repositories. Known for Phase 2: `InMemoryLoanRepository.get` scans the whole list, which is O(n).

---

## Phase 2: Data structures

| # | Question | Choice |
|---|---|---|
| D1 | How are the benchmarks measured? | Median of several runs, setup outside the timer |
| D2 | How is the catalogue sort written? | One `sorted()` with a tuple key |
| D3 | How are repeats and pairs found in one pass? | A dict or set, one lookup per item |
| D4 | What does option 9 print when it undoes a return? | Same shape as the borrow message, plus the removed fine only when one existed |
| D5 | Where does the waiting-queue logic live? | A `WaitingQueue` class wrapping a deque |
| D6 | Where does the borrowing history live? | Built on demand from the loans |
| D7 | What does `count_items` return for an unknown category? | `None`, like `path_to` |
| D8 | What does an undo entry store? | IDs and numbers, never the `Loan` object |

### D1. Benchmarks
- **What:** the median of several runs (7 by default, 3 for the hand-written sorts, 21 for searches under a millisecond), with setup outside the timer.
- **Why:** the median ignores the odd slow run, and building 50,000 books costs far more than the call being measured. Results under 1 ms are noisy: the shape (flat, linear, quadratic) is reliable, the exact ratios are not.

### D2. Catalogue sort
- **What:** one `sorted()` with the key `(top_category(item.category), -item.pages, item.title)`.
- **Why:** one pass and one readable line. Tuples compare field by field, and negating the pages reverses only that field (this works for numbers only). Rejected: three stable passes and `cmp_to_key`.

### D3. Repeats, grouping, counting and two-sum
- **What:** a dict or set that remembers what has been seen: a dict from ISBN to its first title, a `defaultdict(list)`, a `Counter`, and a dict from pages to item.
- **Why:** a lookup is O(1) on average, so each task is one pass, O(n), instead of a nested loop's O(n²). Sorting first costs O(n log n) and loses line numbers and catalogue order.

### D4. Undo-return message
- **What:** `OK: Undid return of 'The Alchemist' by Rahul Mehta (loan L001 is open again, fine of ₹100 removed).` The fine part appears only when a fine was recorded.
- **Why:** the brief gives no sample. This has the same shape as the borrow message and names both things that change. The text is built in `format_undone`, so `Library` still prints nothing.

### D5. Waiting queue
- **What:** a `WaitingQueue` class in `dsa/waiting_queue.py` that wraps a `deque`. `Library` calls `join`, `leave`, `place_of` and `rejoin`.
- **Why:** the queue's rules (nobody queued twice, places count from 1, rejoin at a place for undo) live in one class tested alone, and Phase 3 only has to change this class. Rejected: raw deques inside `Library`.

### D6. Borrowing history
- **What:** `Library.borrow_history(member_id)` builds a linked list (`BorrowHistory`) from the member's loans on every call, newest first.
- **Why:** the loans stay the single source of truth, so the history cannot disagree with them and an undone borrow needs no extra code. The cost is O(L log L) for one member's loans. Rejected: a stored history, which is a second copy to keep in step.

### D7. `count_items` for an unknown category
- **What:** it returns `None`, like `path_to`.
- **Why:** `0` would look like a real answer and hide a typo. `None` forces the caller to handle "no such category", and mypy checks it.

### D8. What an undo entry stores
- **What:** only IDs and numbers (action, loan ID, member ID, ISBN, place in the queue, fine). The stack keeps the last 20 actions, and undoing something that has gone raises a clear error.
- **Why:** a `Loan` is a live object that can change or disappear after it was saved, and the queue place and fine are not on the loan at all. Rejected: pushing the `Loan` itself or a snapshot of the whole library.

---

## Phase 3: SQL

| # | Question | Choice |
|---|---|---|
| D1 | Is availability stored or calculated? | Calculated: total copies minus open loans |
| D2 | What does ON DELETE do for each foreign key? | RESTRICT on all |
| D3 | How do reference items count in Q11? | Included, with their copy count |
| D4 | Which Phase 2 structures survive a restart? | Both: waiting list and undo history, each in a table |
| D5 | Which database? | SQLite |

### D1. Availability
- **What:** calculated, not stored: total copies minus the open loans, counted with a `LEFT JOIN`.
- **Why:** the loans are the single source of truth, so the number can never drift. It also matches Phase 1 D2. I would store it only if a measured `EXPLAIN` showed the count was too slow.

### D2. ON DELETE
- **What:** RESTRICT on every foreign key.
- **Why:** loans and fines are history and money. A delete that would orphan them is refused until a person deals with it, so one `DELETE` can never erase them.

### D3. Reference items in Q11
- **What:** included, with their copy count (the Encyclopaedia shows 1 available).
- **Why:** Q11 asks for the copies on the shelf per title, which is a plain count, and it matches the brief's expected output exactly.

### D4. What survives a restart
- **What:** both the waiting list (the `reservations` table) and the undo history (a table of its own).
- **Why:** a restart should not lose a member's place in the queue or the chance to fix the last mistake. Undo entries already hold only IDs and numbers (Phase 2 D8), so they can be stored as rows.

### D5. Database
- **What:** SQLite.
- **Why:** it is built into Python, needs no install, and gives a fresh temporary database for every test, which Part B needs.

---

## Phase 4: API and website

| # | Question | Choice |
|---|---|---|
| D1 | Which status code for each exception? | 404 missing, 422 bad input, 409 state conflict, 500 unexpected |
| D2 | Threads with a lock, or `async def`? | `async def` with no `await`, one shared connection |
| D3 | Which origins does CORS allow? | Only `http://localhost:5173` (from `WEB_ORIGIN`) |
| D4 | Who checks the ISBN? | Python, not Pydantic |
| D5 | Where does the search state live? | The URL query string |
| D6 | Tailwind or Material UI? | Tailwind CSS |

### D1. Status codes
- **What:** 404 for missing things (item, member, loan). 422 for bad input (bad ISBN, blank or invalid values, missing fields). 409 for rule or state conflicts (R1, R2, R3, R4, R6, R7, R8, loan already returned, waiting-list errors, duplicate ISBN). 500 for anything unexpected, with a plain message.
- **Why:** 404 means it does not exist, 409 means it exists but its state conflicts, and 422 means the input makes no sense. `ValidationError` has two meanings, so it is split by its `field`: `waiting_list` and `duplicate_isbn` are 409, the rest are 422. All codes match the brief's 4.0 sample.

### D2. `async def` endpoints with one shared connection
- **What:** every endpoint is `async def` with no `await` inside, and the server shares one SQLite connection.
- **Why:** SQLite's connection can only be used from the thread that made it. This runs all requests on one thread, one at a time, so no lock is needed. Two members borrowing the last copy at the same moment are handled in turn: the second one sees the true state and gets R7.

### D3. CORS
- **What:** only `http://localhost:5173` is allowed (from `WEB_ORIGIN`), for `GET` and `POST`.
- **Why:** allowing `*` would let any website call the API from a member's browser.

### D4. ISBN checked in Python, not in Pydantic
- **What:** the request schema takes `isbn` as a plain string.
- **Why:** the server must keep the last word, and the message has to match the console character for character. Pydantic would return its own message and the wrong error code.

### D5. Where the search state lives
- **What:** the search text, category and sort live in the URL query string (`useSearchParams`). Each details link carries that query string, and "Back to results" uses it.
- **Why:** state inside the catalogue page is lost when the page unmounts, so "Back to results" would show an empty search. The URL survives navigation, reload, the browser's back button and a shared link, and no extra state needs to be kept in sync.

### D6. Tailwind CSS for styling
- **What:** Tailwind CSS (v4, through its Vite plugin) for all styling. Shared class strings live in `src/ui.js`, and the old plain CSS file was removed.
- **Why:** my components were already semantic and had working labels, so Tailwind could be added without rewriting them, whereas Material UI would have replaced my own buttons, inputs, table and toast. The 360 px layout is controlled in the markup (`grid sm:grid-cols-3`, `flex-wrap`). Trade-off: long `className` strings, and accessibility (labels, focus, keyboard) is mine to handle, which I checked by hand.