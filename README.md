# LibraryHub Mini

A small library system for the City Knowledge Library, built in four phases:
object-oriented Python, data structures, a SQL database, and a web site on top of
an HTTP API. A member can search the catalogue, open a book, fill a basket and
borrow it, from a console menu or from the browser, against the same engine and
the same database.

| Phase | Topic | What it adds |
|---|---|---|
| 1 | Python and OOP | The rules R1 to R10, domain classes, the `Library` service, a console menu |
| 2 | Data structures | Search, sorting, hash table, undo stack, waiting queue, linked list, category tree, benchmarks |
| 3 | SQL | A normalised SQLite database, queries, transactions, indexes, a unit of work |
| 4 | The website | A FastAPI HTTP API and a React site (Tailwind CSS) |

## Contents

1. [Quick start](#quick-start)
2. [Configuration](#configuration)
3. [The console menu](#the-console-menu)
4. [The website](#the-website)
5. [The HTTP API](#the-http-api)
6. [Project layout](#project-layout)
7. [Business rules](#business-rules)
8. [What each phase added](#what-each-phase-added)
9. [Tests and checks](#tests-and-checks)
10. [Documentation index](#documentation-index)
11. [Future work](#future-work)
12. [Troubleshooting](#troubleshooting)


---

## Quick start

**You need:** Python 3.10 or newer, Node.js with npm, and git.
Check with `python --version`, `node --version` and `npm --version`.

### 1. Get the code

```
git clone https://github.com/Laya-projects/library_hub.git
cd library_hub
```

### 2. Set up Python

Windows (PowerShell):

```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e . pytest pytest-cov ruff mypy fastapi uvicorn httpx
```

macOS or Linux:

```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e . pytest pytest-cov ruff mypy fastapi uvicorn httpx
```

If PowerShell refuses to activate the environment, run
`Set-ExecutionPolicy -Scope Process RemoteSigned` once and try again.

### 3. Start the API (terminal 1)

The sample data is built around the date **2026-10-12**. Set `TODAY` so the
overdue loans and fines come out the same for everyone.

Windows (PowerShell):

```
$env:TODAY="2026-10-12"
python -m uvicorn api.main:app --port 8000
```

macOS or Linux:

```
TODAY=2026-10-12 python -m uvicorn api.main:app --port 8000
```

Open <http://localhost:8000/docs> to try every endpoint in the browser.
`GET /health` answers when the server is up.

### 4. Start the website (terminal 2)

Windows (PowerShell):

```
cd web
npm install
Copy-Item .env.example .env
npm run dev
```

macOS or Linux:

```
cd web
npm install
cp .env.example .env
npm run dev
```

Open <http://localhost:5173>. The site needs the API from step 3 to be running.

### 5. Or use the console menu

```
$env:TODAY="2026-10-12"; python -m libraryhub.main
```

On macOS or Linux: `TODAY=2026-10-12 python -m libraryhub.main`.

The first run creates `library.db` and fills it from the starter CSV files. After
that the database is the source of truth. To start again from the starter data,
delete `library.db`.

---

## Configuration

| Variable | Used by | Default | Meaning |
|---|---|---|---|
| `TODAY` | API and console | the real date | The date the program pretends it is. Must look like `2026-10-12`. |
| `LIBRARY_DB` | console | `library.db` | Path of the SQLite file. |
| `WEB_ORIGIN` | API | `http://localhost:5173` | The one browser origin allowed by CORS. |
| `VITE_API_URL` | website | `http://localhost:8000` | Where the website finds the API. Set in `web/.env`. |

`web/.env` is ignored by git. `web/.env.example` is committed as a template.

---

## The console menu

Type a number and press Enter. `0` exits.

| Choice | What it does | What you type | Example result |
|--------|--------------|---------------|----------------|
| 1 | List the catalogue | nothing | A table. `2 of 2` means both copies are free, `0 of 1` means the only copy is out, `not borrowable` is a reference item. |
| 2 | Search by title or author (ignores case) | a word, e.g. `paulo` | `1 result:` and the matching items, or `No items match 'zzz'.` |
| 3 | Borrow | member ID, then ISBN | `OK: Asha Raman borrowed 'Wings of Fire'. Due 2026-10-26.` If every copy is out it asks `Join the waiting list? (y/n)`. |
| 4 | Return | loan ID | `OK: Rahul Mehta returned 'The Alchemist'. Late by 20 days. Fine: ₹100.` Adds `Next on waiting list: <name>.` when someone is waiting. |
| 5 | Renew | loan ID | `OK: Renewed 'Sapiens' (renewal 1 of 2). New due date ...` Refused for magazines, at the renewal limit, or when someone is waiting. |
| 6 | Join the waiting list | member ID, then ISBN | `OK: Asha Raman is #1 on the waiting list for 'The Alchemist'.` |
| 7 | Member loans | member ID | The member's current loans, `OVERDUE (20 days)` when late, how many items they hold out of their limit, and their unpaid fines. |
| 8 | Overdue report | nothing | Every late loan, longest overdue first, with the fine so far and totals. |
| 9 | Undo last borrow/return | nothing | Reverses the latest borrow or return (up to the last 20 actions), or prints `Nothing to undo.` |
| 0 | Exit | nothing | Quits the program. |

Money is whole rupees (`₹100`). Dates are `YYYY-MM-DD`. Errors look like
`ERROR [R3]: ...` for a rule violation and `ERROR [ClassName]: ...` otherwise.

Handy IDs from the sample data: member `M001` (Asha Raman), book `9780000000011`
(Wings of Fire), loan `L001`, book `9780000000028` (The Alchemist, all copies out,
so borrowing it offers the waiting list).

**A short story to try** (borrow, waiting list, return):

1. `3`, `M001`, `9780000000028`: no copies are free, so it asks about the waiting
   list. Answer `y`.
2. `4`, `L001`: the copy comes back, and the output ends with
   `Next on waiting list: Asha Raman.`

**Persistence check:** borrow `9780000000011` as `M001`, leave with `0`, start the
program again and choose `7` for `M001`. Loan `L011` is still there.

---

## The website

A React site that talks to the API. It never applies a business rule itself: it may
check things early for the member's comfort, but the server has the last word.

### Screens

| Route | Screen | What a member does |
|---|---|---|
| `/` | Catalogue | Search, filter by category, sort, add to basket or join the waiting list |
| `/books/:isbn` | Book details | See one book and its availability; "Back to results" restores the search |
| `/me` | My loans | See active loans, due dates, overdue status and unpaid fines |
| `/basket` | Basket | Borrow every item, one after another, and see each server message |
| `/admin/add` | Add item | The librarian's form, with checks under each field |
| `*` | Not found | A friendly page with a link back |

The member is chosen from the picker in the navbar (no passwords). Switching member
starts a new, empty basket.

### Behaviour worth knowing

- **Search state lives in the URL** (`?q=py&category=...&sort=title`), so the back
  button and "Back to results" work.
- **Typing is debounced** (300 ms) and an old request is cancelled with
  `AbortController`, so a slow old response never overwrites a newer one.
- **Every screen that fetches data** shows loading, error (with a Retry button) and
  empty states.
- **The basket limit** (3, 5 or 10 items by membership) is checked in React for
  comfort and again in Python, which is the one that must never be removed.
- **Server messages are shown exactly as sent**, including the `₹` sign.

### Accessibility and responsive design

- Styled with **Tailwind CSS v4** (see `DECISIONS.md` for why).
- Every screen works at **360 px** wide: one column, no sideways page scrolling.
- Every input has a `<label>`; errors are linked to their field with
  `aria-describedby`; loading and result messages use `role="status"`, errors use
  `role="alert"`.
- The whole site works with the keyboard only (Tab, Enter), with a visible focus
  ring and a "Skip to content" link.

### Website commands

Run these inside `web/`:

```
npm run dev       # development server on http://localhost:5173
npm run build     # production build
npm run preview   # serve the production build
npm run lint      # oxlint
```

---

## The HTTP API

FastAPI, in front of the same `Library` service the console uses. One `Library` is
built at startup and closed at shutdown. Endpoints are `async def` with no `await`
inside, because the single SQLite connection may only be used from one thread (see
`DECISIONS.md`).

### Endpoints

| Endpoint | Success | What it does |
|---|---|---|
| `GET /health` | `200` | Is the server up |
| `GET /books?q=&sort=&category=` | `200` list | Search or list items; `sort` is `title` (default), `pages` or `category` |
| `GET /books/{isbn}` | `200` | One book, or 404 |
| `GET /categories` | `200` list | Top-level category names for the filter |
| `GET /members` | `200` list | Members for the navbar picker |
| `GET /members/{id}/loans` | `200` | A member's active loans and unpaid fines |
| `POST /loans` `{member_id, isbn}` | `201 {loan_id, due_date}` | Borrow |
| `POST /loans/{loan_id}/return` | `200 {loan_id, days_late, fine, next_in_waiting_list}` | Return |
| `POST /reservations` `{member_id, isbn}` | `201 {position}` | Join the waiting list |
| `POST /books` | `201` | Add an item (librarian) |

### Errors

Every error has the same body, and the message is the same text as the console:

```json
{ "error": "<code>", "message": "<same text as the console>" }
```

| Situation | Status |
|---|---|
| Item, member or loan not found | `404` |
| Invalid ISBN or bad input | `422` |
| A rule conflicts with the current state (R1, R2, R3, R4, R6, R7, R8, loan already returned, already queued) | `409` |
| Anything unexpected | `500`, with a plain message and never the Python error text |

The reasons for each choice are in `DECISIONS.md`.

CORS allows only the origin in `WEB_ORIGIN`.

---

## Project layout

```
library_hub/
├─ data/                   CSV starter data (books, members, loans)
├─ src/libraryhub/
│  ├─ items.py             Book, Reference and Magazine (polymorphic items)
│  ├─ members.py           Student, Regular and other member types
│  ├─ loans.py             Loan and Fine
│  ├─ calculations.py      Pure functions: due dates, fines, limits
│  ├─ errors.py            Every error, with its code and message
│  ├─ repositories.py      Storage interfaces and the in-memory versions
│  ├─ csv_loader.py        Reads the CSV files into the repositories
│  ├─ library.py           The Library service: where the rules are applied
│  ├─ unit_of_work.py      Each business operation commits or rolls back as one
│  ├─ audit.py             @audit decorator and the audit log
│  ├─ formatters.py        Turns data into the exact text of the menu
│  ├─ menu.py              The console menu (no rules inside)
│  ├─ main.py              Starts everything; reads TODAY
│  ├─ dsa/                 Phase 2: search, sorting, hashing, queue, history, categories
│  └─ storage/             Phase 3: Database and one SQLite repository per table
├─ api/                    Phase 4: the FastAPI app
│  ├─ main.py              create_app(library, today) and the real startup
│  ├─ errors.py            Exception to status code and JSON body
│  └─ schemas.py           Request bodies and response shapes
├─ web/                    Phase 4: the Vite + React site
│  ├─ .env.example         VITE_API_URL=http://localhost:8000
│  └─ src/
│     ├─ components/       Navbar, Layout, BookCard, BookList, BookActions,
│     │                    AvailabilityBadge, SearchBar, CategoryFilter,
│     │                    SortSelect, AddItemForm, LoadingSpinner
│     ├─ pages/            CataloguePage, BookDetailsPage, MyLoansPage,
│     │                    BasketPage, AddItemPage, NotFoundPage
│     ├─ context/          MemberContext, BasketContext (useReducer), ToastContext
│     ├─ hooks/            useBooks, useDebouncedValue
│     ├─ api.js            apiGet and apiPost helpers
│     └─ ui.js             Shared Tailwind class strings
├─ sql/                    schema.sql, seed.sql, queries.sql, tx_demo.sql, run_sql.py
├─ experiments/            injection_demo.py
├─ tests/                  pytest tests, including test_api.py
├─ docs/                   Design notes, benchmarks, reports (see the index below)
├─ benchmarks.py
├─ DECISIONS.md            Design decisions and why
└─ README.md
```

How the layers fit: domain classes at the bottom, then pure calculations,
repositories, the `Library` service, and then three front doors on top: the console
menu, the HTTP API and (through the API) the website. None of the front doors
applies a rule itself; they ask `Library` and show the answer.

---

## Business rules

| Rule | What it says | Enforced in | Tests |
|------|--------------|-------------|-------|
| R1 | Reference items can never be borrowed | `Library._check_borrowable`, `ItemNotBorrowableError` | TODO |
| R2 | Magazines get 7 days and cannot be renewed | `Library.renew` (via `item.max_renewals()`), `calculations.due_date` | TODO |
| R3 | Each membership has an item limit | `Library._check_limit`, `Member.borrow_limit` | TODO |
| R4 | Borrowing is blocked when unpaid fines are above ₹100 | `Library._check_fines`, `calculations.exceeds_fine_limit` | TODO |
| R5 | A fine is capped at the item's price | `Loan.fine` and `calculations` | TODO |
| R6 | Renewals are limited, and not allowed while someone waits | `Library.renew`, `RenewalNotAllowedError` | TODO |
| R7 | No free copy: offer the waiting list, first come first served | `Library._check_available`, `Library.reserve`, `Library._place_in_line` | TODO |
| R8 | A member cannot hold two copies of the same title | `Library._check_no_duplicate`, `DuplicateLoanError` | TODO |
| R9 | An ISBN is exactly 13 digits | `items.validate_isbn`, `InvalidISBNError` | TODO |
| R10 | Returning on the due date is not late | `Loan.days_late` | TODO |

---

## What each phase added

### Phase 1: Python and OOP

Domain classes (`Book`, `Magazine`, `Reference`, member types, `Loan`), an exception
hierarchy where each error carries its rule code, pure calculation functions, a
repository layer, the `Library` service with its ordered rule checks, the `@audit`
decorator, and the console menu.

### Phase 2: data structures

| Feature | Structure | File | Tests |
|---|---|---|---|
| Find an item by title or ISBN | linear and binary search | `dsa/search.py` | `tests/test_search.py` |
| Sort the catalogue and reports | bubble, insertion, selection (hand-written) and `sorted(key=)` | `dsa/sorting.py` | `tests/test_sorting.py` |
| Look up items and members by ID | hash table | `dsa/hashing.py` | `tests/test_hashing.py` |
| Undo the last borrow or return | stack (`deque`, last 20 actions) | `library.py` (`undo`) | `tests/test_library.py`, `tests/test_menu.py` |
| Waiting list | queue (`WaitingQueue`) | `dsa/waiting_queue.py` | `tests/test_waiting_queue.py` |
| Borrowing history | singly linked list | `dsa/history.py` | `tests/test_history.py` |
| Category tree and counts | tree with recursive walks | `dsa/categories.py` | `tests/test_categories.py` |
| Recursion warm-ups | factorial, fibonacci, digit sum, recursive binary search | `dsa/recursion.py` | `tests/test_recursion.py` |
| Big test data | fake book generator | `dsa/fake_books.py` | `tests/test_fake_books.py` |

Benchmarks:

```
python benchmarks.py                 # everything (hand-written sorts at 10,000 take minutes)
python benchmarks.py --quick         # hand-written sorts only up to 5,000
python benchmarks.py --only audit    # or: sorts, queue
```

The full report, with predicted against measured Big-O, is in
[docs/benchmarks.md](docs/benchmarks.md). Headlines:

- At 10,000 books, `sorted(key=)` is about 830 times faster than insertion sort.
- At 10,000 books, binary search takes about 0.003 ms against about 1 ms for linear search.
- `borrow` and `return_item` grow in a straight line with the number of loans.

### Phase 3: durable data (SQL)

Loans, fines, members and the catalogue live in a SQLite database, so they survive
closing the program. `Library` never mentions SQL, and the same tests pass on the
in-memory repositories and on the database.

| Piece | Where |
|---|---|
| Normalisation write-up (flat file to 1NF, 2NF, 3NF) | `docs/normalisation.md`, `library_flat.csv` |
| ER diagram with the cardinality of every relationship | `docs/er_diagram.md` |
| Schema (keys, NOT NULL, UNIQUE, CHECKs, ON DELETE RESTRICT) | `sql/schema.sql` |
| Seed data (7 items, 5 members, 10 loans, 4 fines, 3 open loans) | `sql/seed.sql` |
| The 12 queries, each with its question and join explained | `sql/queries.sql` |
| Transaction demo: a broken borrow rolls back and leaves no trace | `sql/tx_demo.sql` |
| Index report (`EXPLAIN QUERY PLAN` before and after) | `docs/index_report.md` |
| `storage/` package: `Database` and one repository per table | `src/libraryhub/storage/` |
| Unit of work: commit or roll back as one | `src/libraryhub/unit_of_work.py` |
| Injection experiment and its saved output | `experiments/injection_demo.py`, `docs/injection_evidence.txt` |

To build and query a database with the SQL files directly:

```
python sql/run_sql.py library.db sql/schema.sql sql/seed.sql
python sql/run_sql.py library.db sql/queries.sql
```

### Phase 4: the website

An HTTP API (`api/`) in front of the existing engine, and a React site (`web/`).

| Part | What it covers |
|---|---|
| A0 to A3 | FastAPI app, read and write endpoints, one place that maps exceptions to responses, CORS, `tests/test_api.py` |
| B1 and B2 | Wireframes, component tree, components and props |
| B3 | Controlled inputs, `useEffect`, debounce, `AbortController` |
| B4 | Loading, error, empty and results views; the Add item form |
| B5 | React Router, with the search kept in the URL |
| B6 | Member and basket context, `useReducer`, checkout |
| B7 | Tailwind styling, 360 px layout, labels, keyboard use |

The component tree and the note on where each piece of state lives are in
[docs/component_tree.md](docs/component_tree.md).

---

## Tests and checks

Python (from the project root, with the virtual environment active):

```
python -m pytest
python -m pytest --cov=libraryhub --cov-report=term-missing
python -m ruff check .
python -m mypy src
```

- All tests pass with total coverage of 90% or more, and `ruff` and `mypy` report no problems.
- `library_world` tests run twice, once on each backend (`[memory]` and `[sqlite]`).
- `tests/test_api.py` runs the API with FastAPI's `TestClient` on the in-memory world.
- `tests/test_no_string_sql.py` fails if any SQL in `src/` is built from text.

Website (from `web/`):

```
npm run lint
npm run build
```

Manual checks for the site: use it at 360 px wide (browser DevTools, device
toolbar) with the keyboard only, and with the network throttled to "Slow 3G" to
confirm that an old response never replaces a newer one.

---

## Documentation index

| File | What is in it |
|---|---|
| [DECISIONS.md](DECISIONS.md) | Every design decision and why (including Tailwind, URL search state, status codes, async endpoints) |
| [docs/normalisation.md](docs/normalisation.md) | Flat file to 3NF, with the three anomalies |
| [docs/er_diagram.md](docs/er_diagram.md) | ER diagram and cardinalities |
| [docs/index_report.md](docs/index_report.md) | Indexes, before and after |
| [docs/benchmarks.md](docs/benchmarks.md) | Phase 2 benchmarks |
| [docs/injection_evidence.txt](docs/injection_evidence.txt) | SQL injection experiment output |
| [docs/component_tree.md](docs/component_tree.md) | React component tree and where state lives |
| `docs/` screenshots | The five screens, with loading, empty and error states |

---

## Future work

Ideas that go beyond the Phase 4 brief, from the smallest to the largest:

| Idea | What it needs |
|---|---|
| **Return button on My loans** | React only: the API already has `POST /loans/{loan_id}/return`. Show the fine and any "next on waiting list" message. |
| **Renew button on My loans** | A new `POST /loans/{loan_id}/renew` calling `Library.renew`, with R2 and R6 mapped to `409`, plus a test and the button. |
| **Add member (librarian)** | `Library.add_member` inside the unit of work, a `POST /members` endpoint with validation and a duplicate-ID error, tests, and a form like Add item. |
| **Edit and delete items** | `PUT` and `DELETE` endpoints for books, with the `ON DELETE RESTRICT` rule from Phase 3 (an item that has loans cannot be deleted). |
| **Login and roles** | Real sign-in, so only librarians can open Add item. Today the member picker has no passwords. |
| **Pay fines** | An endpoint and a screen to mark a fine as paid, which would also lift an R4 block. |
| **Production setup** | Dockerfile for the API and the site, HTTPS, and a real `WEB_ORIGIN`. |
| **AI library assistant** | A chatbot that answers questions such as "anything on Python for beginners?" (see below). |

### AI library assistant

A chat box that finds books by meaning, using embeddings and a pre-trained model from Hugging Face. Planned order:

1. **Add descriptions to the catalogue.** Today a book has only a title, authors and a category, which is too little text to search by meaning.
2. **Add semantic search only, with embeddings and no LLM:** `GET /books/semantic?q=`. Keep the vectors in memory or in a small vector store such as FAISS or Chroma. It is cheap and useful by itself.
3. **Add the LLM on top.** Retrieve the top few books, fetch their live availability from `Library`, and ask the model to answer only from those facts.
4. **Add the chat box in React,** with loading, empty and error states like every other screen.

Rules for building it:

- **Read-only.** The assistant never borrows, returns or reserves. Those stay on the existing buttons, so the server keeps the last word.
- **Live facts are never indexed.** Index only static text (title, authors, category, description). Availability, loans and fines come from `Library` at answer time, so the bot never reports a stale number.
- **Keep the model off the API's one thread.** The `async def` endpoints and the single SQLite connection depend on requests being quick. Run the model as a separate service, or in a worker thread that never touches the database connection.

## Troubleshooting

| Problem | Fix |
|---|---|
| The site shows "Can't reach the library server." | Start the API (step 3) and check that `VITE_API_URL` in `web/.env` matches its address. |
| The browser blocks the request and the console mentions CORS | The site must run on the origin in `WEB_ORIGIN` (default `http://localhost:5173`). Restart the API after changing it. |
| Overdue loans and fines look different from this README | Set `TODAY=2026-10-12` before starting the API or the console. |
| I want the starter data back | Delete `library.db` and start again. |
| PowerShell will not activate `.venv` | `Set-ExecutionPolicy -Scope Process RemoteSigned`, then activate again. |
| `ModuleNotFoundError: libraryhub` | Activate `.venv` and run `python -m pip install -e .` from the project root. |
| `ModuleNotFoundError: api` | Run `uvicorn` from the project root, not from inside `api/`. |
| Port 8000 or 5173 is already in use | Stop the other program, or choose another port and update `WEB_ORIGIN` and `VITE_API_URL` to match. |
| Editor complains about a file name differing only in casing | Rename the file so its name matches the import exactly (Windows ignores case, Linux and Docker do not). |