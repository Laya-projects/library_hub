# Workflow: Phase 1

## Step 0: Professional setup *(new)*

- Git repo, `src/` layout, virtual environment, `pyproject.toml`.
- `pytest`, plus `ruff` (linting) and `mypy` (type checking) from day one.
- A basic `Dockerfile` and a `Jenkinsfile` skeleton that runs the tests.

## Step 1: Analyse the rules, on paper

- Underline nouns and verbs in the rulebook, as the brief says.
- Build a rule traceability table (R1-R10 → method → test). The brief only asks for this at the end. We start it first and fill it in as we go.
- Draw the class diagram and CRC cards.

## Step 2: Error system

- The exception hierarchy from the brief, with each error carrying its rule code (R3, R4, ...).
- One place that formats messages, so the `ERROR [R3]: ...` text can't drift. Phase 4's API reuses this.

## Step 3: Domain models

- Abstract `LibraryItem` with `Book`, `Magazine` and `ReferenceItem`.
- Abstract `Member` with `Student`, `Regular` and `Premium`, using polymorphism so there is no `if member_type ==` anywhere.
- `Loan` with the due date and fine logic.
- **Upgrades:** dataclasses, `Enum` for types, money stored as integer rupees, and validation through properties.

## Step 4: Pure calculation functions *(new)*

- Due date, days late and fine (R2, R5, R10) as small functions with no side effects.
- `today` is always passed in, so the worked-example tables become instant parametrized tests.

## Step 5: Repository layer *(new, the biggest optimisation)*

- Interfaces for storing items, members and loans, with an in-memory version loaded from the CSVs.
- `Library` never touches CSV files directly. In Phase 3, you swap in a database version without changing `Library`.

## Step 6: Library service

- `borrow`, `return_item`, `renew`, `reserve`, `member_loans` and `overdue_report`.
- **Upgrade:** the 7-step check order becomes a list of small rule checks run in sequence. Adding or reordering a rule becomes a one-line change.

## Step 7: Pythonic layer

- The `@audit` decorator, the `iter_overdue` generator, and comprehensions with `sorted(key=lambda)`.
- **Extra:** Python's `logging` module instead of prints, and `functools.wraps` done properly.

## Step 8: Console menu

- The menu only handles input and output; all logic stays in `Library`.
- A separate formatter for the tables, so the spacing matches the samples exactly.
- Bad input never crashes it.

## Step 9: Testing

- 20+ tests is the brief's floor. We aim for 35-40, with a coverage target of 90%+.
- Every sample transcript becomes a golden test, which compares output to the expected text.
- Fixtures build a fresh state for every test.

## Step 10: Wrap-up

- `README` with run instructions, `DECISIONS.md` (at least 3 entries), the traceability table, and Docker plus Jenkins running green.

# Phase 2 : DSA 


| Step | What | Output |
| :--- | :--- | :--- |
| **0** | **Setup:** new branch `feature/dsa`, new folder `src/libraryhub/dsa/`, a timing helper, and a generator that makes big test data (1,000 to 100,000 items) | Skeleton, test data generator |
| **1** | **Analysis:** list where Phase 1 scans lists or loops, and write a Big-O table for each current operation | Notes in `docs/`, first `DECISIONS.md` entry |
| **2** | **Searching:** linear search and binary search by ISBN or title on a sorted catalogue | Search functions plus tests |
| **3** | **Sorting:** write two or three sorts yourself (for example insertion, merge, quick), make them stable, compare with `sorted()`, and use one for the reports | Sort functions plus tests |
| **4** | **Hashing:** your own hash table with chaining for ISBN to item and member ID to member, handling collisions | Hash table class, an index used by the Library |
| **5** | **Stack:** undo. Borrow, return and renew become small command objects, and an undo stack reverses the last one | Undo stack plus tests, wired into the menu |
| **6** | **Queue:** waiting list. Replace the dictionary of lists with a real queue class, keeping first-come-first-served | Queue class, Library updated |
| **7** | **Linked list:** a singly linked list for the borrowing history (append, iterate, reverse, remove) | Linked list class plus tests |
| **8** | **Recursion:** walk the category tree, count and flatten items, and a recursive binary search | Recursive functions plus tests |
| **9** | **Benchmarks:** time each version at several sizes, make a results table (and an optional chart), and write a short explanation of why one wins | `docs/benchmarks.md` |
| **10** | **Wrap-up:** tests, ruff and mypy clean, coverage at 90% or more, README section, `DECISIONS.md` with at least 3 new entries, pull request | Phase 2 finished |


