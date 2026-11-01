from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from libraryhub.csv_loader import load_data
from libraryhub.errors import ItemNotAvailableError
from libraryhub.library import Library
from libraryhub.loans import Loan
from libraryhub.storage.database import Database
from libraryhub.storage.items import SqliteItemRepository
from libraryhub.storage.loans import SqliteFineRepository, SqliteLoanRepository
from libraryhub.storage.members import SqliteMemberRepository
from libraryhub.unit_of_work import NullUnitOfWork

TODAY = date(2026, 10, 12)
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ALCHEMIST = "9780000000028"  # 0 of 1 available
WINGS = "9780000000011"


@pytest.fixture
def db():
    database = Database(":memory:")
    database.execute("CREATE TABLE scratch (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
    yield database
    database.close()


@pytest.fixture
def sqlite_world():
    """A Library on a fresh in-memory SQLite database, filled from data/."""
    Loan.reset_numbering()
    database = Database(":memory:")
    items = SqliteItemRepository(database)
    members = SqliteMemberRepository(database)
    loans = SqliteLoanRepository(database)
    fines = SqliteFineRepository(database)
    load_data(DATA_DIR, items, members, loans, fines)
    library = Library(items, members, loans, fines, unit_of_work=database)
    yield SimpleNamespace(library=library, db=database, loans=loans, fines=fines)
    database.close()


def ids(database):
    return [row["id"] for row in database.fetch_all("SELECT id FROM scratch ORDER BY id")]


def add(database, number):
    database.execute("INSERT INTO scratch VALUES (?, ?)", (number, f"row {number}"))


# --- Database.transaction ------------------------------------------------------


def test_a_finished_block_is_committed(db):
    with db.transaction():
        add(db, 1)
        assert db.in_transaction  # still open inside the block
    assert not db.in_transaction
    assert ids(db) == [1]


def test_an_exception_rolls_back_every_change_and_is_raised_again(db):
    with pytest.raises(RuntimeError, match="boom"), db.transaction():
        add(db, 1)
        add(db, 2)
        raise RuntimeError("boom")
    assert ids(db) == []  # not only the last statement: both are gone
    assert not db.in_transaction


def test_a_database_error_in_the_middle_rolls_back_the_earlier_statements(db):
    with pytest.raises(Exception, match="NOT NULL"), db.transaction():
        add(db, 1)
        db.execute("INSERT INTO scratch VALUES (2, NULL)")
    assert ids(db) == []


def test_changes_made_before_the_block_are_not_touched(db):
    add(db, 1)  # outside any block: saved at once
    with pytest.raises(RuntimeError), db.transaction():
        add(db, 2)
        raise RuntimeError
    assert ids(db) == [1]


def test_nested_blocks_commit_once_at_the_end(db):
    with db.transaction():
        with db.transaction():
            add(db, 1)
        assert db.in_transaction  # the inner block did not commit
        add(db, 2)
    assert not db.in_transaction
    assert ids(db) == [1, 2]


def test_an_inner_failure_that_is_caught_undoes_only_the_inner_part(db):
    with db.transaction():
        add(db, 1)
        with pytest.raises(ValueError), db.transaction():
            add(db, 2)
            raise ValueError
        add(db, 3)
    assert ids(db) == [1, 3]


def test_a_failing_outer_block_undoes_even_inner_blocks_that_finished(db):
    with pytest.raises(RuntimeError), db.transaction():
        with db.transaction():
            add(db, 1)
        raise RuntimeError
    assert ids(db) == []


def test_the_database_works_again_after_a_failure(db):
    with pytest.raises(RuntimeError), db.transaction():
        raise RuntimeError
    with db.transaction():
        add(db, 1)
    assert ids(db) == [1]


def test_the_null_unit_of_work_just_runs_the_block():
    calls = []
    with NullUnitOfWork().transaction():
        calls.append("ran")
    assert calls == ["ran"]


def test_the_null_unit_of_work_does_not_hide_exceptions():
    with pytest.raises(ValueError), NullUnitOfWork().transaction():
        raise ValueError


# --- Library operations are all or nothing -----------------------------------------


def test_a_borrow_that_fails_after_the_loan_is_stored_leaves_no_loan(
    sqlite_world, monkeypatch
):
    world = sqlite_world
    loans_before = len(world.loans.list_all())
    original_add = world.loans.add

    def add_then_fail(loan):
        original_add(loan)  # the INSERT really happens...
        raise RuntimeError("disk full")  # ...and then something goes wrong

    monkeypatch.setattr(world.loans, "add", add_then_fail)
    with pytest.raises(RuntimeError, match="disk full"):
        world.library.borrow("M001", WINGS, TODAY)
    assert len(world.loans.list_all()) == loans_before
    assert not world.db.in_transaction


def test_a_return_that_fails_after_the_fine_is_saved_leaves_no_fine(
    sqlite_world, monkeypatch
):
    world = sqlite_world
    fines_before = [fine.loan_id for fine in world.fines.list_all()]

    def fail(loan):
        raise RuntimeError("disk full")

    monkeypatch.setattr(world.loans, "update", fail)
    with pytest.raises(RuntimeError, match="disk full"):
        world.library.return_item("L001", TODAY)  # 20 days late: the fine goes first
    assert [fine.loan_id for fine in world.fines.list_all()] == fines_before
    assert world.library.get_loan("L001").is_open()
    assert not world.db.in_transaction


def test_a_refused_borrow_changes_nothing_and_leaves_no_transaction_open(sqlite_world):
    world = sqlite_world
    loans_before = len(world.loans.list_all())
    with pytest.raises(ItemNotAvailableError):
        world.library.borrow("M001", ALCHEMIST, TODAY)
    assert len(world.loans.list_all()) == loans_before
    assert not world.db.in_transaction
    assert world.library.undo() is None  # nothing was remembered


def test_a_finished_borrow_is_stored_and_can_be_undone(sqlite_world):
    world = sqlite_world
    loan = world.library.borrow("M001", WINGS, TODAY)
    assert not world.db.in_transaction
    assert world.loans.get(loan.loan_id) is not None
    world.library.undo()
    assert world.loans.get(loan.loan_id) is None


def test_an_undo_that_fails_changes_nothing_and_can_be_tried_again(
    sqlite_world, monkeypatch
):
    world = sqlite_world
    world.library.return_item("L001", TODAY)  # records a fine
    fines_after_return = len(world.fines.list_all())
    working_update = world.loans.update

    def fail(loan):
        raise RuntimeError("disk full")

    monkeypatch.setattr(world.loans, "update", fail)
    with pytest.raises(RuntimeError, match="disk full"):
        world.library.undo()  # removes the fine, then fails to reopen the loan
    assert len(world.fines.list_all()) == fines_after_return  # the removal was undone

    monkeypatch.setattr(world.loans, "update", working_update)
    result = world.library.undo()  # the entry was kept, so this now works
    assert result is not None and result.action == "return"
    assert len(world.fines.list_all()) == fines_after_return - 1
    assert world.library.get_loan("L001").is_open()