"""Fixtures shared by several test files.

`library_world` runs every test that uses it TWICE: once on the in-memory
repositories and once on a fresh in-memory SQLite database (`[memory]` and
`[sqlite]` in the test names). Both must give the same answers, which is what
"the Phase 1 and Phase 2 tests pass unchanged on the database" means.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest

from libraryhub.csv_loader import load_data
from libraryhub.library import Library
from libraryhub.loans import Loan
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

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _build_memory_world(loans=None):
    """A fresh Library on in-memory repositories, built from the real data/ folder."""
    Loan.reset_numbering()  # loan numbers are shared state, so start clean
    items = InMemoryItemRepository()
    members = InMemoryMemberRepository()
    loans = InMemoryLoanRepository() if loans is None else loans
    fines = InMemoryFineRepository()
    load_data(DATA_DIR, items, members, loans, fines)
    return SimpleNamespace(
        library=Library(items, members, loans, fines),
        items=items,
        members=members,
        loans=loans,
        fines=fines,
    )


def _build_sqlite_world(databases):
    """A fresh Library on a fresh SQLite database (in memory), same data."""
    Loan.reset_numbering()
    database = Database(":memory:")
    databases.append(database)  # so the fixture can close it afterwards
    items = SqliteItemRepository(database)
    members = SqliteMemberRepository(database)
    loans = SqliteLoanRepository(database)
    fines = SqliteFineRepository(database)
    with database.transaction():  # all the data or none of it
        load_data(DATA_DIR, items, members, loans, fines)
    return SimpleNamespace(
        library=Library(items, members, loans, fines, unit_of_work=database),
        items=items,
        members=members,
        loans=loans,
        fines=fines,
        db=database,
    )


@pytest.fixture(params=["memory", "sqlite"])
def backend(request):
    return request.param


@pytest.fixture
def make_world(backend):
    """A function that builds a fresh world.

    Pass a loan repository to swap it. A test that does so is checking how
    Library talks to a repository, so it always gets the in-memory world.
    """
    databases = []

    def build(loans=None):
        if loans is not None or backend == "memory":
            return _build_memory_world(loans)
        return _build_sqlite_world(databases)

    yield build
    for database in databases:
        database.close()


@pytest.fixture
def library_world(make_world):
    """A fresh Library (with its repositories) for every test."""
    return make_world()


@pytest.fixture
def world(library_world):
    """The older name that test_library.py uses."""
    return library_world