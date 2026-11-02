"""Entry point: wires the layers together and starts the menu.

    $env:TODAY="2026-10-12"; python -m libraryhub.main     (PowerShell)

Run as a program, the data lives in library.db in the project folder, so a loan
survives closing and reopening. The first run fills it from the CSV files.
Set LIBRARY_DB to use another file. Called as a function with no LIBRARY_DB, the
program uses the in-memory repositories, as in Phase 1 and 2.

TODAY is read here, once, and handed down. Nothing below this file reads the
clock, so the same data and the same TODAY always give the same output.
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from libraryhub.csv_loader import load_data
from libraryhub.library import Library
from libraryhub.loans import Loan
from libraryhub.menu import Menu
from libraryhub.repositories import (
    InMemoryFineRepository,
    InMemoryItemRepository,
    InMemoryLoanRepository,
    InMemoryMemberRepository,
)
from libraryhub.storage.database import Database
from libraryhub.storage.items import SqliteItemRepository
from libraryhub.storage.loans import SqliteFineRepository, SqliteLoanRepository
from libraryhub.storage.members import SqliteMemberRepository

if TYPE_CHECKING:
    from collections.abc import Mapping

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DEFAULT_DB = DATA_DIR.parent / "library.db"  # the project folder
LOG_FILE = "libraryhub.log"


def parse_today(environ: Mapping[str, str]) -> date:
    """TODAY=YYYY-MM-DD if set, otherwise the real date. Bad text raises ValueError."""
    text = environ.get("TODAY", "").strip()
    if not text:
        return date.today()
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"TODAY must look like 2026-10-12 (YYYY-MM-DD), not '{text}'."
        ) from None


def build_library(data_dir: Path = DATA_DIR) -> Library:
    """Create empty repositories, fill them from the CSV files, return the Library."""
    Loan.reset_numbering()
    items = InMemoryItemRepository()
    members = InMemoryMemberRepository()
    loans = InMemoryLoanRepository()
    fines = InMemoryFineRepository()
    load_data(data_dir, items, members, loans, fines)
    return Library(items, members, loans, fines)


def build_sqlite_library(
    db_path: str | Path, data_dir: Path = DATA_DIR
) -> tuple[Library, Database]:
    """Open (or create) the database and return the Library and the open Database.

    A database with no items and no members is filled from the CSV files, in one
    transaction. After that the CSV files are never read again: the database is
    the truth. The caller must close the Database.
    """
    Loan.reset_numbering()  # the loan repository moves it past the stored loans
    database = Database(db_path)
    items = SqliteItemRepository(database)
    members = SqliteMemberRepository(database)
    loans = SqliteLoanRepository(database)
    fines = SqliteFineRepository(database)
    if items.count() == 0 and members.count() == 0:
        with database.transaction():
            load_data(data_dir, items, members, loans, fines)
    library = Library(items, members, loans, fines, unit_of_work=database)
    return library, database


def setup_logging(log_file: str = LOG_FILE) -> None:
    """Log to a file, never to the screen, so the menu output stays clean."""
    logging.basicConfig(
        filename=log_file,
        encoding="utf-8",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main(environ: Mapping[str, str] | None = None) -> int:
    environ = os.environ if environ is None else environ
    # Windows consoles default to a legacy code page that cannot print ₹.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    try:
        today = parse_today(environ)
    except ValueError as error:
        print(f"ERROR: {error}")
        return 2

    setup_logging()
    database: Database | None = None
    db_path = environ.get("LIBRARY_DB", "").strip()
    if db_path:
        library, database = build_sqlite_library(db_path)
    else:
        library = build_library()
    print(f"LibraryHub Mini - today is {today.isoformat()}")
    try:
        Menu(library, today, input, print).run()
    finally:
        if database is not None:
            database.close()
    return 0


if __name__ == "__main__":
    # A copy of the environment, so running the module never changes os.environ.
    run_environ = {**os.environ}
    run_environ.setdefault("LIBRARY_DB", str(DEFAULT_DB))
    raise SystemExit(main(run_environ))