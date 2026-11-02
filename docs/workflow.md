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


# Phase 3 plan: Durable data (SQL)

**Part A** is design and SQL, on paper and in `.sql` files.
**Part B** connects your Python engine to the database.



**Branch:** `feature/sql`, created after Phase 2 (`feature/dsa`) was finished.

---

## Part A: Design and SQL

| # | Step | What you do | Files you produce | Status |
|---|---|---|---|---|
| 0 | **Setup** | Create `sql/` and the branch. Check `sqlite3` works in Python and in a SQLite shell or editor. | `sql/`, `sql/run_sql.py` | [x] |
| 1 | **Flat file (3.1)** | Join the 3 starter CSVs into one row per loan with the 16 columns of the brief. Write 3 anomalies with real rows: update, insert (Divya Rao, who never borrowed) and delete. | `library_flat.csv`, `docs/normalisation.md` | [x] |
| 2 | **Normalise (3.2)** | Take the flat file to 1NF (authors in one `A;B` cell), 2NF, then 3NF (membership type to limits, category to parent). Show before and after at each step. List the final tables. | `docs/normalisation.md` | [x] |
| 3 | **ER diagram and schema (3.3)** | Draw the ER diagram and show the cardinality of every relationship. Write `schema.sql` with PK, FK, NOT NULL, UNIQUE (ISBN, email) and CHECKs (due date not before issue date, copies and fine not negative). Choose ON DELETE on purpose for every FK. | `sql/schema.sql`, `docs/er_diagram.md` | [x] |
| 4 | **Seed (3.4)** | Load the CSVs with `seed.sql` or a loader script. Counts: 7 items, 7 authors, 5 members, 10 loans, 4 fines, 8 categories, 3 open loans. | `sql/seed.sql` | [x] |
| 5 | **Query pack (3.5)** | The 12 queries, each with its business question as a comment and a note on which join you used and why. | `sql/queries.sql` | [x] |
| 6 | **Transactions (3.6a)** | Borrow as one transaction (check availability, insert the loan, insert the audit row). Break it on purpose at the audit insert, show that ROLLBACK leaves no L011, then run the correct version. | `sql/tx_demo.sql` | [x] |
| 7 | **Indexes (3.6b)** | Generate 100,000 loans, pick the 2 slowest queries, run `EXPLAIN QUERY PLAN` before and after an index. Name one index you chose not to create and say why. | `docs/index_report.md` | [x] |

**Query batches (step 5)**
- **Q1 to Q4:** the warm-up (JOIN, WHERE, GROUP BY, LIMIT).
- **Q5, Q6, Q8, Q11:** LEFT JOIN, a subquery or NOT EXISTS. Ask what you must keep when there is no match.
- **Q7, Q9, Q10, Q12:** the hard ones (month grouping, HAVING, date differences, a self-join on loans).

**Things that trip you up**
- Q7 groups by the month the item was **returned**, not issued.
- Q10 counts only returned loans.
- Q3 and Q6 depend on `TODAY = 2026-10-12`, so never use `date('now')`.
- 8 categories means the 7 used by items plus Technology.
- Q11 lists the Encyclopaedia with 1 available (decision D3).

---

## Part B: Python meets the database

| # | Step | What you do | Files | Status |
|---|---|---|---|---|
| 8 | **`storage/` package (3.7a)** | `Database` (connection, schema, transactions) and one repository class per table, using `sqlite3` with `?` placeholders only. They plug into the existing repository interfaces, so `Library` barely changes. | `src/libraryhub/storage/` | [x] |
| 9 | **Unit of work (3.7b)** | A context manager so each business operation commits or rolls back as one. `Library` depends on a small `UnitOfWork` interface, and `Database` implements it (savepoints for nested blocks). Memory (undo stack, waiting queue) changes only after the commit. | `src/libraryhub/unit_of_work.py`, `tests/test_unit_of_work.py` | [x] |
| 10 | **Phase 1 and 2 tests on the database (3.7c)** | `conftest` builds a fresh database per test, so every `library_world` test runs on `[memory]` and `[sqlite]`. Persistence check: borrow, close, reopen, option 7 shows L011. Two fixes were needed: `FineRepository.update`, and `Member` equality by value. | `tests/conftest.py`, `src/libraryhub/main.py`, `tests/test_persistence.py` | [x] |
| 11 | **Injection experiment (3.8)** | `search_unsafe` (f-string) and `search_safe` (parameterised) in a throwaway file. Reproduce the 4 outputs (1, 7, 0, 1 rows) and save them as evidence. | `experiments/injection_demo.py`, `docs/injection_evidence.txt`, `tests/test_injection.py` | [x] |
| 12 | **Wrap-up** | ruff, mypy, pytest; coverage 90% or more; check no SQL is built from text; update the README and DECISIONS; open the PR. | `tests/test_no_string_sql.py`, README, DECISIONS.md | [ ] confirm |

**Step 12 checklist (tick when true)**
- [ ] `python -m ruff check .` passes
- [ ] `python -m mypy src` passes
- [ ] `python -m pytest --cov=libraryhub --cov-report=term-missing` all green, total 90% or more
- [ ] counts after loading: 7 items, 5 members, 10 loans, 4 fines, 3 open loans
- [ ] all 12 query results match the brief (`docs/queries_output.txt`)
- [ ] rolled-back transaction leaves no trace (`docs/tx_demo_output.txt`)
- [ ] no SQL built from text in `src/` (`tests/test_no_string_sql.py`)
- [ ] Dockerfile copies `sql/`
- [ ] README Phase 3 section, DECISIONS.md and the pull request done

---

## Running the SQL files

```
python sql/run_sql.py library.db sql/schema.sql sql/seed.sql
python sql/run_sql.py library.db sql/queries.sql
python sql/run_sql.py :memory: sql/schema.sql sql/seed.sql sql/queries.sql
```

On your office laptop, plain script mode could not read `.sql` files, so you used the
`runsql` PowerShell function instead (it runs the same helper through `python -c`):

```powershell
function runsql { python -c "import sys; sys.argv = ['run_sql.py'] + sys.argv[1:]; exec(open(r'C:\Users\laya_r\OneDrive - LevelShift\library_hub\sql\run_sql.py', encoding='utf-8').read())" @args }
```

To reset the real database, delete `library.db`. Git ignores `*.db`.
