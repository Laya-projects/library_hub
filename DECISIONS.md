# DECISIONS.md

Decision log for LibraryHub Mini. Each entry: the problem, the options, what I chose and why.

---

## Phase 1: Python + OOP

### D1. Where do unpaid fines live? (R4, R5)

**Problem.** R4 blocks borrowing when a member's unpaid fines are above ₹100. Something has to answer "how much does this member owe?". With the starter data, Karthik (M004) has two unpaid fines, ₹80 (L009) and ₹40 (L010), so he owes ₹120 and is blocked. His paid fines and other members' fines must not count.

**Options.**
- **A. A stored number on `Member`** (`unpaid_fines = 120`). Simple to read, but it is a second copy of the truth. Paying a fine means updating the fine and the member's number. Forgetting one gives a wrong R4 answer.
- **B. A `Fine` record (`loan_id`, `amount`, `paid`) with the total calculated on demand.** One source of truth. A `Fine` knows its loan, not its member, so the lookup goes fine -> loan -> member.

**Chosen: B.** `Member` stores no fine total. `Library` holds the list of `Fine` records and calculates the member's unpaid total when R4 is checked (sum of amounts where `paid` is false and the loan belongs to that member).

**Why.** Never store something that can be calculated, because stored copies go stale. Paying a fine becomes flipping one `paid` flag. It also matches `fines.csv` exactly and the later `fines` table in Phase 3.

**Check.** Karthik must come out at ₹120.

---

### D2. Who calculates availability of a title?

**Problem.** `total_copies` says how many copies exist (Python Crash Course has 2). Nothing says how many are free now. Availability is the total minus the loans of that ISBN that have no return date. Python Crash Course has 2 copies and L002 is still open, so 1 is available. Storing a separate "available" number would go stale on every borrow and return.

**Options.**
- **A. `Library` calculates it.** `available_copies(isbn)` = `total_copies` minus the count of open loans for that ISBN. `Library` already holds both items and loans. Easy to test. It scans the loan list, which is fine at this size and is something Phase 2 can measure and improve.
- **B. A repository calculates it.** A separate data-access class, in Phase 3 backed by a SQL `COUNT(*)` query. Fast later, but it adds a class the brief does not ask for in Phase 1.

**Chosen: A.** Items store only `total_copies`. `Library.available_copies(isbn)` is the single place that calculates availability.

**Why.** It is the simplest design that keeps one source of truth. In Phase 3 this one method can move behind a repository on purpose, so the later change is planned and small.

---

### D3. Does a `Loan` hold member and item objects, or their IDs?

**Problem.** A loan links one member to one item, for example L002 links M004 to ISBN 9780000000042. The link can be stored as live objects or as IDs.

**Options.**
- **A. Hold the objects** (`loan.member`, `loan.item`). Convenient, since the fine calculation can reach the rate and price directly. But a loan tied to live objects can go stale if they are reloaded, and a database row can only store IDs, so Phase 3 needs conversion.
- **B. Hold only IDs** (`member_id`, `isbn`). Matches `loans.csv` and a database row exactly. The loan cannot look anything up itself, so calculations take the member and item as inputs.
- **C. Hold IDs, and have `Library` hand over the objects when needed.** This is B with the lookup made explicit.

**Chosen: B.** `Loan` stores `member_id` and `isbn` (plus loan number, issue date, due date, return date and renewal count). Its calculations receive what they need, for example `loan.fine(today, member, item)`. `Library` does the lookups in its dicts.

**Why.** The IDs in the CSV files and the future database already are the link. The library's dicts stay the single source of truth, so a loan can never hold an outdated copy of a member or item. The Phase 3 database swap becomes easier.

**Consequence for the design.** In the class diagram the `Loan` -> `Member` and `Loan` -> `LibraryItem` links become "refers to by ID".

---

## Phase 2: DSA

(Entries to be added in Phase 2.)

## Phase 3: Database

(Entries to be added in Phase 3.)

## Phase 4: React

(Entries to be added in Phase 4.)