"""The database repositories behave like the in-memory ones (Phase 3, Part B)."""

from datetime import date
from pathlib import Path

import pytest

from libraryhub.csv_loader import load_data
from libraryhub.errors import LoanNotFoundError, ValidationError
from libraryhub.items import Book, Magazine
from libraryhub.loans import Fine, Loan
from libraryhub.members import RegularMember, StudentMember
from libraryhub.storage import (
    Database,
    SqliteFineRepository,
    SqliteItemRepository,
    SqliteLoanRepository,
    SqliteMemberRepository,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture
def db():
    Loan.reset_numbering()
    database = Database()  # a fresh in-memory database for every test
    yield database
    database.close()


@pytest.fixture
def repos(db):
    return {
        "items": SqliteItemRepository(db),
        "members": SqliteMemberRepository(db),
        "loans": SqliteLoanRepository(db),
        "fines": SqliteFineRepository(db),
    }


def make_book(isbn="9780000000011", title="Wings of Fire", authors=None, **kw):
    return Book(
        isbn,
        title,
        authors or ["A.P.J. Abdul Kalam", "Arun Tiwari"],
        kw.get("category", "Biography"),
        kw.get("parent"),
        180,
        250,
        2,
    )


# --- Setup --------------------------------------------------------------------


def test_the_schema_is_built_and_membership_types_are_filled(db):
    tables = {
        row["name"]
        for row in db.fetch_all("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    assert {"items", "members", "loans", "fines", "audit_log"} <= tables
    types = db.fetch_all("SELECT type FROM membership_types ORDER BY type")
    assert [row["type"] for row in types] == ["Premium", "Regular", "Student"]


def test_opening_an_existing_database_keeps_its_data(tmp_path):
    path = tmp_path / "library.db"
    first = Database(path)
    SqliteMemberRepository(first).add(StudentMember("M001", "Asha", "a@example.com"))
    first.close()
    second = Database(path)  # the schema step must not run again
    assert SqliteMemberRepository(second).count() == 1
    second.close()


# --- Items --------------------------------------------------------------------


def test_item_round_trip_keeps_authors_in_order(repos):
    repos["items"].add(make_book())
    item = repos["items"].get("9780000000011")
    assert isinstance(item, Book)
    assert item.title == "Wings of Fire"
    assert item.authors == ["A.P.J. Abdul Kalam", "Arun Tiwari"]
    assert (item.pages, item.price, item.total_copies) == (180, 250, 2)


def test_item_parent_category_comes_back(repos):
    repos["items"].add(
        make_book(
            "9780000000042",
            "Python",
            ["Eric"],
            category="Programming",
            parent="Technology",
        )
    )
    item = repos["items"].get("9780000000042")
    assert (item.category, item.parent_category) == ("Programming", "Technology")


def test_item_type_decides_the_class(repos):
    magazine = Magazine(
        "9780000000073", "India Today", ["Various"], "Magazines", None, 90, 80, 3
    )
    repos["items"].add(magazine)
    assert isinstance(repos["items"].get("9780000000073"), Magazine)


def test_missing_item_is_none(repos):
    assert repos["items"].get("9780000000999") is None


def test_duplicate_isbn_is_refused_with_the_phase_1_message(repos):
    repos["items"].add(make_book())
    with pytest.raises(ValidationError) as caught:
        repos["items"].add(make_book())
    assert caught.value.message == "An item with ISBN 9780000000011 already exists."
    assert repos["items"].count() == 1


def test_a_shared_author_is_stored_once(repos, db):
    repos["items"].add(make_book("9780000000011", "One", ["Various"]))
    repos["items"].add(make_book("9780000000028", "Two", ["Various"]))
    assert db.fetch_one("SELECT COUNT(*) AS n FROM authors")["n"] == 1


def test_a_value_the_database_rejects_becomes_a_validation_error(repos):
    book = make_book()
    book._price = -1  # skips the Python check, so the database CHECK is what stops it
    with pytest.raises(ValidationError) as caught:
        repos["items"].add(book)
    assert caught.value.message.startswith("Item cannot be stored")


def test_list_all_keeps_the_order_items_were_added(repos):
    for isbn, title in [("9780000000028", "Second"), ("9780000000011", "First")]:
        repos["items"].add(make_book(isbn, title, ["X"]))
    assert [item.title for item in repos["items"].list_all()] == ["Second", "First"]


# --- Members ------------------------------------------------------------------


def test_member_round_trip(repos):
    repos["members"].add(RegularMember("M002", "Rahul Mehta", "rahul@example.com"))
    member = repos["members"].get("M002")
    assert isinstance(member, RegularMember)
    assert (member.name, member.email) == ("Rahul Mehta", "rahul@example.com")


def test_duplicate_member_id_message(repos):
    repos["members"].add(StudentMember("M001", "Asha", "asha@example.com"))
    with pytest.raises(ValidationError) as caught:
        repos["members"].add(StudentMember("M001", "Other", "other@example.com"))
    assert caught.value.message == "A member with ID M001 already exists."


def test_duplicate_email_is_refused(repos):
    repos["members"].add(StudentMember("M001", "Asha", "same@example.com"))
    with pytest.raises(ValidationError) as caught:
        repos["members"].add(StudentMember("M002", "Other", "same@example.com"))
    assert "same@example.com" in caught.value.message


def test_a_member_the_database_rejects_becomes_a_validation_error(repos):
    member = StudentMember("M001", "Asha", "asha@example.com")
    member._email = "no-at-sign"  # skips the Python check, the database CHECK stops it
    with pytest.raises(ValidationError) as caught:
        repos["members"].add(member)
    assert caught.value.message.startswith("Member cannot be stored")


def test_members_keep_the_order_they_were_added(repos):
    repos["members"].add(StudentMember("M009", "Zed", "z@example.com"))
    repos["members"].add(StudentMember("M001", "Abe", "a@example.com"))
    assert [m.member_id for m in repos["members"].list_all()] == ["M009", "M001"]
    assert repos["members"].count() == 2


# --- Loans and fines ------------------------------------------------------------


def seed_people_and_item(repos):
    repos["items"].add(make_book())
    repos["members"].add(StudentMember("M001", "Asha", "a@example.com"))
    repos["members"].add(RegularMember("M002", "Rahul", "r@example.com"))


def make_loan(loan_id="L001", member="M001", isbn="9780000000011", returned=None):
    return Loan(
        member,
        isbn,
        date(2026, 9, 1),
        date(2026, 9, 15),
        loan_id=loan_id,
        return_date=returned,
    )


def test_loan_round_trip_and_open_filters(repos):
    seed_people_and_item(repos)
    repos["loans"].add(make_loan("L001"))
    repos["loans"].add(make_loan("L002", "M002", returned=date(2026, 9, 10)))
    assert repos["loans"].get("L002").return_date == date(2026, 9, 10)
    assert [loan.loan_id for loan in repos["loans"].list_open()] == ["L001"]
    assert [loan.loan_id for loan in repos["loans"].list_for_member("M002")] == ["L002"]
    assert len(repos["loans"].list_for_isbn("9780000000011")) == 2
    assert [loan.loan_id for loan in repos["loans"].list_all()] == ["L001", "L002"]


def test_duplicate_loan_id_message(repos):
    seed_people_and_item(repos)
    repos["loans"].add(make_loan())
    with pytest.raises(ValidationError) as caught:
        repos["loans"].add(make_loan())
    assert caught.value.message == "A loan with ID L001 already exists."


def test_update_saves_return_date_and_renewals(repos):
    seed_people_and_item(repos)
    repos["loans"].add(make_loan())
    loan = repos["loans"].get("L001")
    loan.return_date = date(2026, 9, 20)
    loan.renewals = 1
    repos["loans"].update(loan)
    again = repos["loans"].get("L001")
    assert (again.return_date, again.renewals) == (date(2026, 9, 20), 1)


def test_update_and_remove_of_an_unknown_loan(repos):
    with pytest.raises(LoanNotFoundError):
        repos["loans"].update(make_loan("L404"))
    with pytest.raises(LoanNotFoundError):
        repos["loans"].remove("L404")


def test_remove_deletes_the_loan(repos):
    seed_people_and_item(repos)
    repos["loans"].add(make_loan())
    repos["loans"].remove("L001")
    assert repos["loans"].get("L001") is None


def test_a_loan_for_an_unknown_member_is_refused(repos):
    repos["items"].add(make_book())
    with pytest.raises(ValidationError):
        repos["loans"].add(make_loan(member="M404"))


def test_the_loan_counter_continues_after_a_restart(tmp_path):
    path = tmp_path / "library.db"
    first = Database(path)
    repos = {
        "items": SqliteItemRepository(first),
        "members": SqliteMemberRepository(first),
        "loans": SqliteLoanRepository(first),
    }
    seed_people_and_item(repos)
    repos["loans"].add(make_loan("L001"))
    repos["loans"].add(make_loan("L011"))
    first.close()

    Loan.reset_numbering()  # a new program run starts with the counter at 1
    second = Database(path)
    SqliteLoanRepository(second)  # opening the repository moves the counter on
    assert (
        Loan("M001", "9780000000011", date(2026, 10, 12), date(2026, 10, 26)).loan_id
        == "L012"
    )
    second.close()


def test_fine_round_trip_and_remove(repos):
    seed_people_and_item(repos)
    repos["loans"].add(make_loan())
    repos["fines"].add(Fine("L001", 100, paid=False))
    fines = repos["fines"].list_all()
    assert [(f.loan_id, f.amount, f.paid) for f in fines] == [("L001", 100, False)]
    repos["fines"].remove_for_loan("L001")
    assert repos["fines"].list_all() == []


def test_a_second_fine_for_the_same_loan_is_refused(repos):
    seed_people_and_item(repos)
    repos["loans"].add(make_loan())
    repos["fines"].add(Fine("L001", 100))
    with pytest.raises(ValidationError) as caught:
        repos["fines"].add(Fine("L001", 50))
    assert caught.value.message == "A fine for loan L001 already exists."


def test_a_fine_for_an_unknown_loan_is_refused(repos):
    with pytest.raises(ValidationError) as caught:
        repos["fines"].add(Fine("L404", 5))
    assert "L404" in caught.value.message


# --- Transactions -----------------------------------------------------------------


def test_a_failed_item_add_leaves_nothing_behind(repos, db):
    repos["items"].add(make_book())
    with pytest.raises(ValidationError):
        repos["items"].add(make_book(authors=["Brand New Author"]))
    assert (
        db.fetch_one(
            "SELECT COUNT(*) AS n FROM authors WHERE name = 'Brand New Author'"
        )["n"]
        == 0
    )


def test_transaction_rolls_back_on_an_error(repos, db):
    seed_people_and_item(repos)
    with pytest.raises(RuntimeError), db.transaction():
        repos["loans"].add(make_loan())
        raise RuntimeError("boom")
    assert repos["loans"].list_all() == []


def test_transaction_commits_when_the_block_ends(repos, db):
    seed_people_and_item(repos)
    with db.transaction():
        repos["loans"].add(make_loan())
    assert len(repos["loans"].list_all()) == 1


def test_nested_transactions_join_the_outer_one(repos, db):
    seed_people_and_item(repos)
    with pytest.raises(RuntimeError), db.transaction():
        with db.transaction():
            repos["loans"].add(make_loan("L001"))
        repos["loans"].add(make_loan("L002", "M002"))
        raise RuntimeError("boom")
    assert repos["loans"].list_all() == []  # the inner block did not commit alone


# --- The starter data, and no SQL built from text ------------------------------------


def test_the_starter_csvs_load_into_the_database(repos):
    load_data(
        DATA_DIR, repos["items"], repos["members"], repos["loans"], repos["fines"]
    )
    assert repos["items"].count() == 7
    assert repos["members"].count() == 5
    assert len(repos["loans"].list_all()) == 10
    assert len(repos["loans"].list_open()) == 3
    assert len(repos["fines"].list_all()) == 4


def test_no_sql_is_built_with_string_formatting():
    storage = Path(__file__).resolve().parent.parent / "src" / "libraryhub" / "storage"
    for source in storage.glob("*.py"):
        text = source.read_text(encoding="utf-8")
        for bad in ('f"SELECT', 'f"INSERT', 'f"UPDATE', 'f"DELETE', ".format(", "% ("):
            assert bad not in text, f"{source.name} builds SQL from text: {bad}"