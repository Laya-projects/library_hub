# DECISIONS.md

Decision log for LibraryHub Mini. Each entry gives the problem, the options, the choice and the reason. A longer version with more detail, up to D7, is kept in `DECISIONS_detailed.md`.

## Phase 1 at a glance

| # | Question | Choice |
|---|---|---|
| D1 | Where do unpaid fines live? | `Fine` records, total calculated when needed |
| D2 | Who works out availability? | `Library.available_copies()` |
| D3 | What does a `Loan` hold? | IDs, not objects |
| D4 | Who writes the error message? | The error class, from raw data |
| D5 | How are models written, and bad values handled? | Plain classes, `ValidationError` |
| D6 | Where does the date and money maths live? | Plain functions in `calculations.py` |
| D7 | How do repositories and the loader work? | `get` returns `None`, loader checks everything first |
| D8 | How is the audit trail recorded and timed? | `@audit` decorator, injectable clock on `AuditLog` |
| D9 | How are edge cases formatted in reports and search? | Singular '1 day', comma authors, explicit empty messages |
| D10 | How does `Library` apply the rules? | Check list, results as data, free copies held for the queue |
| D11 | How does the menu work, and what does a blank search do? | Menu printed once, dictionary dispatch, blank search is an error |

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

### D5. How are the models written, and what happens to bad values?
- **Problem:** an invalid object must never exist (bad ISBN, blank title, negative copies, bad email).
- **Chosen:**
  - Plain classes with `@property` setters that validate at creation. `Fine` is a small `@dataclass`.
  - Bad values raise `ValidationError(field, message)`, which is a `LibraryError`, so the menu catches one family. `InvalidISBNError` stays for ISBNs because the brief names it.
  - `price` and `pages` are checked too. A negative price would make the R5 cap produce a negative fine.
  - `ItemType` is an `Enum`. It is not stored, because the subclass already is the type.
  - The abstract questions (`borrow_limit()`, `loan_period_for(member)` and so on) are methods, as the brief says.
- **Rejected:** keeping `ValueError`. The menu would need to catch two families, and a real bug could be mistaken for bad input.
- **Why:** each object protects itself, so the rest of the code can trust what it receives.

### D6. Where does the date and money maths live? (R2, R4, R5, R6, R10)
- **Problem:** `Loan`, `Library` and the tests all need the same maths, and it must exist in one place.
- **Options:** A) plain functions in `calculations.py`. B) methods on `Loan` and `Member`.
- **Chosen: A.**
- **Why:** pure functions take `today` as a parameter, never read the clock, and can be tested with only numbers and dates. `Loan` calls them, so nothing is duplicated.
- **Details:**
  - `days_late` stops counting at the return date, so a returned loan never gets later.
  - `unpaid_total` raises `KeyError` for a fine whose loan is missing, because quietly skipping it could unblock a member. The loader now stops that data earlier (D7).

### D7. How do the repositories and the loader work?
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

### D8. How is the audit trail recorded and timed?
- **Problem:** we need an audit trail of every successful mutating action (`borrow`, `return_item`, `renew`), without cluttering domain rules or allowing `Library` to read the system clock directly.
- **Options for recording:**
  - A) explicit calls inside each method (`self.audit_log.record(...)`).
  - B) an `@audit(action)` decorator wrapping mutating methods.
- **Options for the clock:**
  - A) reading `datetime.now()` directly inside `Library`.
  - B) an injectable `clock` callable on `AuditLog` / `Library` (defaulting to `datetime.now`).
- **Chosen: B for both.**
- **Why:**
  - An `@audit` decorator separates auditing (a cross-cutting concern) from business logic. Methods focus purely on Rulebook enforcement and state transitions. If a method raises an exception when a rule is broken, the decorator naturally skips recording without error-handling boilerplate.
  - Keeping the clock on `AuditLog` (and injectable via `Library.__init__` or test properties) honors the architecture rule that `Library` never reads the system clock itself. Tests can pass or assign a fixed clock callable to verify audit timestamps deterministically. Scoping `AuditLog` to the `Library` instance prevents test state leakage.
- **Known, for Phase 3:** the audit entry is recorded after the action has happened. If `record` or `_extract_audit_targets` raised, the loan would already be stored but the caller would get an exception. That is a programmer-error case, so it is fine for now; Phase 3's database transactions will fix it properly.

### D9. How are edge cases formatted in reports and search?
- **Problem:** three display formatting questions for search results, member loans, and overdue reports needed decisions.
- **1. OVERDUE (1 days) vs OVERDUE (1 day):**
  - **Options:** A) always plural `"OVERDUE (1 days)"`. B) grammatical singular `"OVERDUE (1 day)"` and plural for others.
  - **Chosen: B.**
  - **Why:** "1 days" is an unpolished pluralization bug. Clean singular/plural logic gives the console UI a professional feel.
- **2. Multiple authors in search results:**
  - **Options:** A) semicolon `; ` matching CSV storage. B) comma `, `.
  - **Chosen: B.**
  - **Why:** semicolon is a storage delimiter in CSV files, whereas comma `, ` is natural English punctuation for reader-facing displays.
- **3. Empty member loans or overdue reports:**
  - **Options:** A) an empty table with naked column headers. B) clear explicit message (`No active loans.` / `No overdue loans.`).
  - **Chosen: B.**
  - **Why:** naked table headers with no rows look broken and confusing. An explicit message gives immediate clarity while preserving the surrounding header and summary counters.

### D10. How does `Library` apply the rules? (R1 to R10)
- **Problem:** `Library` is the only place where the rules are applied, and the menu and the Phase 4 API both call it. Several rule gaps had to be settled.
- **Structure (not a choice between options):**
  - `borrow` runs a list of small checks in the brief's order (R1, R4, R3, R8, availability). The first broken rule raises, and moving a rule is a one-line change.
  - Methods return data (`ReturnResult`, `RenewResult`, `MemberLoans`, `OverdueLine`) or raise a `LibraryError`. They never print, never open files and never read the clock.
  - A `Fine` is stored on return only when the amount is above zero, which matches the starter data (no ₹0 rows).
  - Two errors were added: `LoanNotFoundError` and `LoanAlreadyReturnedError`. The second also stops renewing a returned loan.
  - `return_item` and `renew` call `update(loan)` after changing a loan (see D7).
- **Q1. A copy is free but people are waiting. May someone who isn't first borrow it?**
  - Options: A) no, the copy is held for the queue. B) yes, anyone may take it.
  - **Chosen: A.** The brief says the first person is "served first".
  - How: a member's place is their position in the queue, or one behind the whole queue if they are not in it. They can borrow only if the free copies are at least their place. A spare copy beyond the queue is open to anyone.
  - Cost: the refused member sees "No copies of ... are available", which is slightly loose.
- **Q2. When may someone join the waiting list?**
  - Options: A) refuse three cases. B) allow joining at any time.
  - **Chosen: A.** Refused: a copy is already available to them (a `ValidationError` saying to borrow it), they are already queued (`ValidationError`), or they already hold the title (the R8 error). Reference items can't be waited for (R1).
  - Why: the list stays free of people who could borrow now, and nobody appears twice.
- **Q3. A loan at the renewal limit with someone waiting: which message?**
  - Options: A) the limit message. B) the waiting message.
  - **Chosen: A.** The limit is permanent, whereas "someone is waiting" is temporary, so it would hint that renewing might work later.
  - Check order for `renew`: R2, then the R6 limit, then R6 waiting.
- **Q4. Does `renew` keep a `today` parameter?**
  - Options: A) keep it. B) drop it, because no rule in `renew` depends on the date.
  - **Chosen: A.** `borrow`, `return_item` and `renew` are all called the same way, which keeps the menu and the API simple. The docstring says that `today` is unused: the new due date is the old due date plus the member's loan period (R6).
  - Cost: an argument that does nothing today, and a linter may flag it.
- **Known limits:**
  - The waiting list is a plain `list` of member IDs per ISBN, kept inside `Library`. It is lost when the program closes. Phase 2 swaps it for a `deque` and measures the difference, and Phase 3 moves it behind a repository (the `reservations` table).
  - A free copy is held for the queue, but the refused member still sees "No copies of ... are available". The brief gives only that one message, so it is kept.
  - If the first person in the queue cannot borrow (for example new fines above ₹100), the copy stays held for them. Nothing removes a blocked member from the queue.
  - The R2 check uses `max_renewals() == 0`, so it never asks what type an item is. For a reference item it would also say "Magazines cannot be renewed", but a reference item can never be on loan, so it is unreachable.

### D11. How does the menu work, and what does a blank search do?
- **Problem:** the menu reads input and prints, but every rule must stay in `Library`. Three small questions came up.
- **Q1. What does a blank search do?**
  - Options: A) raise a `ValidationError`. B) return no results.
  - **Chosen: A.** `Library.search_items` raises `ValidationError("query", "Search text cannot be blank.")`, and the menu prints `ERROR [ValidationError]: Search text cannot be blank.`
  - Why: an empty text is inside every title, so a blank search would quietly return the whole catalogue. "No results" would print `No items match ''.`, which looks like a bug. It also matches D5, where bad values raise one error family. The search rule lives in `Library`, not the menu, because the Phase 4 API will use it too.
- **Q2. Is the menu printed once or after every action?**
  - Options: A) print it once at start-up. B) print it again after every action.
  - **Chosen: A.** The brief's samples show `> abc`, the error, and then `> ` again with no menu in between, and Session A shows the prompts following each other directly.
  - Why: it matches the samples character for character, which Step 9's golden tests will compare.
- **Q3. How is a choice turned into an action?**
  - Options: A) a dictionary from `"0"` to `"8"` to methods. B) an `if`/`elif` chain.
  - **Chosen: A.** Adding an option is one new line, and an invalid choice is simply a missing key. It is the same lookup pattern as the CSV loader.
- **Details:**
  - `_ask(prompt)` is the only place that reads input, so stripping happens once.
  - `_handle` is the only place that shows an error, with `error.formatted()`.
  - Input and output are injected (`input_fn`, `output_fn`), so a test can script a whole conversation, and the transcript records `prompt + answer` like a real terminal.
  - End of input (Ctrl+Z) and Ctrl+C leave the loop quietly, with no message, like option 0.
  - `MENU_TEXT` starts at the `===` line. The blank line before it in the brief's sample belongs to `main.py`.
  - Options 3 to 8 print "not built yet" until the later steps.

## Phase 2: DSA

(Entries to be added in Phase 2.)

## Phase 3: Database

(Entries to be added in Phase 3.)

## Phase 4: React

(Entries to be added in Phase 4.)