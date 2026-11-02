# LibraryHub Mini: workflow

## Phase 1: Python and OOP

| # | Step | Description |
|---|---|---|
| 0 | Professional setup | Git repo, `src/` layout, venv, `pyproject.toml`, pytest, ruff, mypy. Basic Dockerfile and Jenkinsfile. |
| 1 | Analyse the rules | Underline nouns and verbs, start the R1-R10 traceability table. Draw the class diagram and CRC cards. |
| 2 | Error system | Exception hierarchy where each error carries its rule code. One place formats the messages. |
| 3 | Domain models | `LibraryItem`, `Member` and `Loan` classes using polymorphism, dataclasses, Enums and integer rupees. |
| 4 | Pure calculations | Due date, days late and fine as side-effect-free functions. `today` is always passed in. |
| 5 | Repository layer | Interfaces plus an in-memory version loaded from the CSVs. `Library` never touches files. |
| 6 | Library service | `borrow`, `return_item`, `renew`, `reserve`, `member_loans`, `overdue_report`. Rule checks run as a list. |
| 7 | Pythonic layer | `@audit` decorator, `iter_overdue` generator, comprehensions and `logging`. |
| 8 | Console menu | Menu only does input and output, with a separate table formatter. Bad input never crashes it. |
| 9 | Testing | 35-40 tests, 90%+ coverage, and every sample transcript as a golden test. |
| 10 | Wrap-up | README, `DECISIONS.md` (3+ entries), traceability table, Docker and Jenkins green. |

## Phase 2: DSA

| # | Step | Description |
|---|---|---|
| 0 | Setup | Branch `feature/dsa`, `dsa/` folder, timing helper and big test-data generator. |
| 1 | Analysis | List where Phase 1 scans lists and write a Big-O table. First `DECISIONS.md` entry. |
| 2 | Searching | Linear and binary search by ISBN or title on a sorted catalogue. |
| 3 | Sorting | Write two or three stable sorts, compare with `sorted()`, and use one for reports. |
| 4 | Hashing | Own hash table with chaining for ISBN to item and member ID to member. |
| 5 | Stack | Undo: borrow, return and renew become command objects on an undo stack. |
| 6 | Queue | Waiting list as a real first-come-first-served queue class. |
| 7 | Linked list | Singly linked list for borrowing history (append, iterate, reverse, remove). |
| 8 | Recursion | Walk the category tree, count and flatten items, recursive binary search. |
| 9 | Benchmarks | Time each version at several sizes and explain why one wins in `docs/benchmarks.md`. |
| 10 | Wrap-up | Tests, lint, 90%+ coverage, README, 3+ new decisions, pull request. |

## Phase 3: SQL

### Part A: Design and SQL

| # | Step | Description |
|---|---|---|
| 0 | Setup | Create `sql/` and the branch `feature/sql`. Check `sqlite3` works. |
| 1 | Flat file | Join the 3 CSVs into one 16-column row per loan. Write the update, insert and delete anomalies. |
| 2 | Normalise | Take the flat file to 1NF, 2NF and 3NF, showing before and after each step. |
| 3 | ER diagram and schema | Draw the ER diagram, write `schema.sql` with PK, FK, UNIQUE, CHECK and chosen ON DELETE rules. |
| 4 | Seed | Load the CSVs and check the counts (7 items, 5 members, 10 loans, 4 fines). |
| 5 | Query pack | The 12 queries, each with its business question and a note on the join used. |
| 6 | Transactions | Borrow as one transaction. Break it on purpose, show the ROLLBACK, then run it correctly. |
| 7 | Indexes | Generate 100,000 loans, find the 2 slowest queries and compare `EXPLAIN QUERY PLAN` before and after. |

### Part B: Python meets the database

| # | Step | Description |
|---|---|---|
| 8 | `storage/` package | `Database` and one repository per table, using `?` placeholders only. |
| 9 | Unit of work | A context manager so each business operation commits or rolls back as one. |
| 10 | Tests on the database | Every `library_world` test runs on both memory and sqlite. Add a persistence check. |
| 11 | Injection experiment | Compare unsafe (f-string) and safe (parameterised) search and save the evidence. |
| 12 | Wrap-up | Lint, mypy, 90%+ coverage, no SQL built from text, README, DECISIONS, pull request. |

## Phase 4: API and React

### Part A: The API

| # | Step | Description |
|---|---|---|
| A0 | Setup | Tiny FastAPI app with `GET /health`, running on port 8000 with `/docs` open. |
| A1 | Read endpoints | One shared `Library` built at startup. `GET` books, categories, members and member loans as `async def`. |
| A2 | Write endpoints and errors | `POST` loans, returns, reservations and books. One handler maps every exception to status plus `{error, message}`. |
| A3 | CORS, TODAY and tests | Allow only `WEB_ORIGIN`, read `TODAY` once, and write one API test per brief sample. |

### Part B: The React site

| # | Step | Description |
|---|---|---|
| B1 | Setup and wireframes | Vite + React app, `.env` with `VITE_API_URL`, five screen sketches and `docs/component_tree.md`. |
| B2 | Components and props | `Navbar`, `Layout`, `BookCard`, `BookList` and `AvailabilityBadge` on hard-coded JSON. |
| B3 | State, events and effects | Controlled search, category and sort with a debounced fetch. `AbortController` stops old responses overwriting new ones. |
| B4 | Conditional rendering, lists, forms | Loading, error, empty and result views, keyed lists, and the Add item form with field errors. |
| B5 | Routing | Routes for catalogue, details, loans, basket, add and 404. Search state lives in the URL query string. |
| B6 | Context, reducer, checkout | `MemberContext` and a basket reducer with the item limit. Checkout calls `POST /loans` one by one and shows server messages exactly. |
| B7 | Styling, responsive, polish | Tailwind or MUI, working at 360 px, labelled inputs and full keyboard use. |
| B8 | Hand-in | README, component tree, screenshots of all five screens, ticked behaviour table and DECISIONS. |