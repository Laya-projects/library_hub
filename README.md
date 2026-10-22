# LibraryHub Mini

A library system built four times: Python + OOP, then data structures, then SQL, then a React website. It enforces the Library Rulebook (R1 to R10) for students, regular readers and premium members.

Status: Phase 1 in progress (Step 1 design done, Step 2 error system).

## Setup

```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
pip install pytest ruff
```

## Run the checks

```
python -m pytest
ruff check .
```

## Project documents

- `DECISIONS.md`: the decision log (problem, options, choice, reason)
- `step1_design_notes.md`: class design, relationships and the abstract contracts

## Rule traceability

Every rule is referred to by number (R1 to R10) in tests, commit messages and documents. The Method and Test columns are filled in as each step is built.

| Rule | Method that enforces it | Test that proves it |
|---|---|---|
| R1 | raises `ItemNotBorrowableError` | |
| R2 | raises `RenewalNotAllowedError.magazine()` | |
| R3 | raises `BorrowLimitExceededError` | |
| R4 | raises `UnpaidFinesError` | |
| R5 | no error (a calculation) | |
| R6 | raises `RenewalNotAllowedError.limit_reached()` or `.someone_waiting()` | |
| R7 | raises `ItemNotAvailableError` | |
| R8 | raises `DuplicateLoanError` | |
| R9 | raises `InvalidISBNError` (prints the class name as its code) | |
| R10 | no error (a calculation) | |