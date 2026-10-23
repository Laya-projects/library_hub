"""Fixtures shared by several test files."""

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

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _build_world(loans=None):
    """A fresh Library built from the real data/ folder."""
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


@pytest.fixture
def make_world():
    """A function that builds a fresh world. Pass a loan repository to swap it."""
    return _build_world


@pytest.fixture
def library_world(make_world):
    """A fresh Library (with its repositories) for every test."""
    return make_world()


@pytest.fixture
def world(library_world):
    """The older name that test_library.py uses."""
    return library_world