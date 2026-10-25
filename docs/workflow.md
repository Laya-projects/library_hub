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