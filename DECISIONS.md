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

| # | Question | Choice |
|---|---|---|
| D1 | How are the benchmarks measured? | Median of several runs, setup outside the timer |
| D2 | How is the catalogue sort written? | One `sorted()` with a tuple key |
| D3 | How do I find repeats and pairs in one pass? | A dict or set, one lookup per item |
| D4 | What does option 9 print when it undoes a return? | OK: Undid return of 'The Alchemist' by Rahul Mehta (loan L001 is open again, fine of ₹100 removed). |

### D1. How are the benchmarks measured? (task 2.1, 2.2)
- **Problem:** one timing run is mostly noise (other programs, garbage collection, a cold cache), so a single number can point to the wrong complexity.
- **Options:** A) time one run. B) the mean of several runs. C) the median of several runs, with the set-up kept outside the timed block.
- **Chosen: C.**
- **Why:** the median ignores the odd slow run, where a mean is dragged up by it. Building a library of 50,000 books costs far more than the call being measured, so only the call itself is timed.
- **Details:**
  - `median_ms` and `median_ms_with_setup` in `dsa/timing.py` use `time.perf_counter()` and report milliseconds.
  - 7 runs by default, 3 for the hand-written sorts (bubble sort at 10,000 books takes seconds), and 21 for searches that take under a millisecond.
  - Results under 1 ms are noisy. The shape (flat, linear or quadratic) is reliable. The exact ratios are not, and the report says so.

### D2. How is the catalogue sort written? (task 2.2)
- **Problem:** the catalogue must be ordered by top-level category ascending, then pages descending, then title ascending. The directions are mixed, so a plain `sorted()` cannot do it in one go.
- **Options:** A) one `sorted()` with a tuple key and the pages negated: `(top_category(item), -item.pages, item.title)`. B) three stable passes (title, then pages, then category). C) `functools.cmp_to_key` with a comparison function.
- **Chosen: A.**
- **Why:** one pass and one readable line. Python compares tuples field by field, so the first field decides and the later ones only break ties. Negating a number reverses its direction. The same key also works with my hand-written sorts, because they take a `key`.
- **Rejected:**
  - B works only because Python's sort is stable, and it is easy to write the passes in the wrong order (the last pass must be the most important key).
  - C is more code and slower, because it calls a Python function for every comparison.
- **Details:**
  - `top_category` maps Programming and Software Engineering to Technology, so they sort together.
  - Negation only works for numbers. A string that had to be descending would need B or C.

### D3. Why dicts and sets for duplicates, grouping, counting and two-sum? (task 2.3)
- **Problem:** four tasks all ask "have I seen this before?" for every item: repeated ISBNs in a CSV, titles per author, how often a title was borrowed, and two books whose pages add up to a target.
- **Options:** A) a nested loop that compares every item with every other item. B) sort first, then compare neighbours. C) a dict or set that remembers what has been seen.
- **Chosen: C.**
- **Why:** a dict or set finds a key in O(1) on average, because the key's hash tells Python where to look. Each item is handled once, so the whole task is one pass, O(n), where the nested loop is O(n²). Sorting first costs O(n log n) and would also lose the original line numbers and the catalogue order.
- **Details:**
  - Duplicates: a dict from ISBN to the title that first used it, so the message can say what the ISBN was "already used by". The line number comes from `reader.line_num`.
  - Grouping: a `defaultdict(list)` from author to titles, with authors sorted A to Z at the end.
  - Counting: `Counter` over the ISBNs of all loans, then sorted by `(-count, title)` so equal counts come out A to Z.
  - Two-sum: a dict from pages to item. Each item first looks for `target - pages` in the dict, and only then adds itself, so an item is never paired with itself. Reference items are skipped because they cannot be borrowed.
  - A dict key must be hashable. Strings, ints and tuples are. A list cannot be a key.

## D4: What does option 9 print when it undoes a return?

**Context.** The brief gives the exact text for undoing a borrow
(`OK: Undid borrow of 'Wings of Fire' by Asha Raman (loan L011 removed).`)
and for "Nothing to undo.", but shows no sample for undoing a return.

**Decision.** Undoing a return prints
`OK: Undid return of 'The Alchemist' by Rahul Mehta (loan L001 is open again, fine of ₹100 removed).`
The fine part appears only when a fine was recorded for that return. Without
a fine the line ends after `is open again)`.

**Reasons.**
- The sentence has the same shape as the borrow message, so the menu reads
  consistently.
- Undoing a return changes two things: the loan opens again, and the fine
  disappears from the member's unpaid total (R4). The message says both, so
  the librarian is not surprised when the total changes.
- The text is built in `format_undone` (formatters.py) from `UndoResult`,
  so `Library` still prints nothing.

**Rejected.** A shorter fixed message (`... (loan L001 reopened).`). It always
reads the same, but it hides that a fine was removed.

**Consequences.** If a later phase shows the brief's own wording for this
case, only `format_undone` and two tests in `test_menu.py` need to change.

## D5: Where does the waiting-queue logic live?

**Context.** Each fully borrowed ISBN needs a first-come, first-served queue of member IDs (R7). Undo must be able to put a member back at their old place.

**Decision.** A `WaitingQueue` class in `dsa/waiting_queue.py` that wraps a `collections.deque`. `Library` calls `join`, `leave`, `place_of` and `rejoin`, and never touches the deque.

**Why.** The queue has its own rules (nobody queued twice, places count from 1, rejoin at a place), and they now live in one class that can be tested alone. Phase 3 moves the queue to a table, so only this class changes.

**Rejected.** Raw deques inside `Library`: less code, but the queue rules end up spread over `borrow`, `reserve` and undo.

## D6: Where does the borrowing history live?

**Context.** The brief wants a singly linked list of a member's loans, newest first.

**Decision.** `Library.borrow_history(member_id)` builds a `BorrowHistory` from the member's loans on every call (oldest first, each inserted at the head).

**Why.** The loan repository stays the only source of truth, so the history cannot disagree with it, and an undone borrow needs no extra code. The cost is O(L log L) for one member's loans, which is small.

**Rejected.** One stored `BorrowHistory` per member: instant to read, but a second copy that every borrow and undo must keep in step.

## D7: What does `count_items` return for an unknown category?

**Decision.** `None`, like `path_to`.

**Why.** `0` would look like a real answer and hide a typo. `None` forces the caller to handle "no such category", and mypy checks it.

**Rejected.** Returning `0`.

## Phase 3: Database

(Entries to be added in Phase 3.)

## Phase 4: React

(Entries to be added in Phase 4.)