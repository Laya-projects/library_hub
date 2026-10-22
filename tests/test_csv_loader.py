from datetime import date
from pathlib import Path

import pytest
from libraryhub.calculations import unpaid_total
from libraryhub.csv_loader import (
    ITEM_CLASSES,
    MEMBER_CLASSES,
    load_data,
    load_fines,
    load_items,
    load_loans,
    load_members,
)
from libraryhub.errors import ValidationError
from libraryhub.items import Book, Magazine, ReferenceItem
from libraryhub.loans import Loan
from libraryhub.members import PremiumMember, RegularMember, StudentMember
from libraryhub.repositories import (
    InMemoryFineRepository,
    InMemoryItemRepository,
    InMemoryLoanRepository,
    InMemoryMemberRepository,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

ITEMS_HEADER = (
    "isbn,title,authors,category,parent_category,item_type,pages,price,total_copies\n"
)
LOANS_HEADER = "loan_id,member_id,isbn,issue_date,due_date,return_date\n"


@pytest.fixture(autouse=True)
def fresh_numbering():
    Loan.reset_numbering()


def write(folder, name, text):
    path = folder / name
    path.write_text(text, encoding="utf-8")
    return path


def fresh_repositories():
    return (
        InMemoryItemRepository(),
        InMemoryMemberRepository(),
        InMemoryLoanRepository(),
        InMemoryFineRepository(),
    )


def write_dataset(folder, *, books=None, members=None, loans=None, fines=None):
    """Write the four files, with a tiny valid default for any left out."""
    default_book = "9780000000011,Wings of Fire,A,Biography,,Book,180,250,2\n"
    default_member = "M001,Asha,asha@example.com,Student\n"
    default_loan = "L001,M001,9780000000011,2026-09-01,2026-09-15,\n"
    write(folder, "books.csv", ITEMS_HEADER + (books or default_book))
    write(
        folder,
        "members.csv",
        "member_id,name,email,membership_type\n" + (members or default_member),
    )
    write(folder, "loans.csv", LOANS_HEADER + (loans or default_loan))
    write(folder, "fines.csv", "loan_id,amount,paid\n" + (fines or "L001,10,no\n"))


def load_real_data():
    items, members, loans, fines = fresh_repositories()
    load_data(DATA_DIR, items, members, loans, fines)
    return items, members, loans, fines


# --- The real starter data ---------------------------------------------------


def test_starter_data_counts():
    items, members, loans, fines = load_real_data()
    assert items.count() == 7
    assert members.count() == 5
    assert len(loans.list_all()) == 10
    assert len(fines.list_all()) == 4
    assert len(loans.list_open()) == 3


def test_the_next_new_loan_is_l011():
    load_real_data()
    new_loan = Loan("M001", "9780000000011", date(2026, 10, 12), date(2026, 10, 26))
    assert new_loan.loan_id == "L011"


def test_starter_items_are_read_correctly():
    items, _, _, _ = load_real_data()
    wings = items.get("9780000000011")
    clean_code = items.get("9780000000035")
    assert type(wings) is Book
    assert wings.authors == ["A.P.J. Abdul Kalam", "Arun Tiwari"]
    assert wings.parent_category is None
    assert (wings.pages, wings.price, wings.total_copies) == (180, 250, 2)
    assert clean_code.parent_category == "Technology"
    assert type(items.get("9780000000066")) is ReferenceItem
    assert type(items.get("9780000000073")) is Magazine


def test_starter_members_get_the_right_class():
    _, members, _, _ = load_real_data()
    assert type(members.get("M001")) is StudentMember
    assert type(members.get("M002")) is RegularMember
    assert type(members.get("M003")) is PremiumMember
    assert members.get("M004").name == "Karthik N"


def test_starter_loans_and_fines_are_read_correctly():
    _, _, loans, fines = load_real_data()
    assert loans.get("L001").return_date is None
    assert loans.get("L004").return_date == date(2026, 9, 24)
    assert loans.get("L003").due_date == date(2026, 10, 20)
    paid = {fine.loan_id: fine.paid for fine in fines.list_all()}
    assert paid == {"L005": True, "L008": True, "L009": False, "L010": False}


def test_karthik_owes_120_after_loading():
    _, _, loans, fines = load_real_data()
    total = unpaid_total("M004", fines.list_all(), loans.list_all())
    assert total == 120


# --- A tiny CSV written by the test ------------------------------------------


def test_two_authors_and_blank_parent_category(tmp_path):
    path = write(
        tmp_path,
        "books.csv",
        ITEMS_HEADER
        + "9780000000011,Wings of Fire,A.P.J. Abdul Kalam;Arun Tiwari,"
        + "Biography,,Book,180,250,2\n"
        + "9780000000035,Clean Code,Robert C. Martin,"
        + "Software Engineering,Technology,Book,464,900,1\n",
    )
    wings, clean_code = load_items(path)
    assert wings.authors == ["A.P.J. Abdul Kalam", "Arun Tiwari"]
    assert wings.parent_category is None
    assert clean_code.authors == ["Robert C. Martin"]
    assert clean_code.parent_category == "Technology"
    assert isinstance(wings.pages, int)
    assert isinstance(wings.price, int)
    assert isinstance(wings.total_copies, int)


def test_quoted_title_with_a_comma_and_non_ascii_text(tmp_path):
    path = write(
        tmp_path,
        "books.csv",
        ITEMS_HEADER
        + '9780000000011,"Café, Society",Zoë Ünal,Fiction,,Book,100,200,1\n',
    )
    (item,) = load_items(path)
    assert item.title == "Café, Society"
    assert item.authors == ["Zoë Ünal"]


def test_blank_return_date_becomes_none(tmp_path):
    path = write(
        tmp_path,
        "loans.csv",
        LOANS_HEADER
        + "L001,M002,9780000000028,2026-09-01,2026-09-22,\n"
        + "L004,M001,9780000000011,2026-09-10,2026-09-24,2026-09-24\n",
    )
    open_loan, returned = load_loans(path)
    assert open_loan.return_date is None
    assert returned.return_date == date(2026, 9, 24)
    assert open_loan.issue_date == date(2026, 9, 1)


@pytest.mark.parametrize(
    ("text", "expected"),
    [("yes", True), ("no", False), ("YES", True), (" No ", False)],
)
def test_paid_text_becomes_a_boolean(tmp_path, text, expected):
    path = write(tmp_path, "fines.csv", f"loan_id,amount,paid\nL005,10,{text}\n")
    (fine,) = load_fines(path)
    assert fine.paid is expected
    assert fine.amount == 10


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Student", StudentMember),
        ("Regular", RegularMember),
        ("Premium", PremiumMember),
    ],
)
def test_member_class_is_chosen_from_the_text(tmp_path, text, expected):
    path = write(
        tmp_path,
        "members.csv",
        f"member_id,name,email,membership_type\nM001,Asha,asha@example.com,{text}\n",
    )
    (member,) = load_members(path)
    assert type(member) is expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [("Book", Book), ("Magazine", Magazine), ("Reference", ReferenceItem)],
)
def test_item_class_is_chosen_from_the_text(tmp_path, text, expected):
    path = write(
        tmp_path,
        "books.csv",
        ITEMS_HEADER + f"9780000000011,Title,Author,Cat,,{text},100,200,1\n",
    )
    (item,) = load_items(path)
    assert type(item) is expected


def test_lookup_keys_match_what_each_class_says_about_itself():
    for text, member_class in MEMBER_CLASSES.items():
        member = member_class("M001", "Asha", "asha@example.com")
        assert member.membership_label() == text
    for text, item_class in ITEM_CLASSES.items():
        item = item_class("9780000000011", "T", ["A"], "C", None, 1, 1, 1)
        assert item.item_type().value == text


def test_load_data_fills_the_four_repositories(tmp_path):
    write(
        tmp_path,
        "books.csv",
        ITEMS_HEADER + "9780000000011,Wings of Fire,A,Biography,,Book,180,250,2\n",
    )
    write(
        tmp_path,
        "members.csv",
        "member_id,name,email,membership_type\nM001,Asha,asha@example.com,Student\n",
    )
    write(
        tmp_path,
        "loans.csv",
        LOANS_HEADER + "L001,M001,9780000000011,2026-09-01,2026-09-15,\n",
    )
    write(tmp_path, "fines.csv", "loan_id,amount,paid\nL001,10,no\n")
    items, members, loans, fines = fresh_repositories()
    load_data(tmp_path, items, members, loans, fines)
    assert (items.count(), members.count()) == (1, 1)
    assert len(loans.list_all()) == 1
    assert len(fines.list_all()) == 1


# --- Bad data gives a clear error, with the file and the line ---------------


def test_bad_price_names_the_file_and_the_line(tmp_path):
    path = write(
        tmp_path,
        "books.csv",
        ITEMS_HEADER
        + "9780000000011,Good,A,Cat,,Book,100,200,1\n"
        + "9780000000028,Bad,A,Cat,,Book,100,abc,1\n",
    )
    with pytest.raises(ValidationError) as caught:
        load_items(path)
    assert "books.csv line 3" in caught.value.message
    assert "price" in caught.value.message


def test_unknown_item_type_is_reported(tmp_path):
    path = write(
        tmp_path,
        "books.csv",
        ITEMS_HEADER + "9780000000011,Title,A,Cat,,Comic,100,200,1\n",
    )
    with pytest.raises(ValidationError) as caught:
        load_items(path)
    assert "Comic" in caught.value.message


def test_bad_isbn_in_the_file_is_reported_with_its_line(tmp_path):
    path = write(
        tmp_path,
        "books.csv",
        ITEMS_HEADER + "123,Title,A,Cat,,Book,100,200,1\n",
    )
    with pytest.raises(ValidationError) as caught:
        load_items(path)
    assert "line 2" in caught.value.message


@pytest.mark.parametrize(
    "bad_date", ["2026-13-01", "12/10/2026", "2026-9-1", "20261012"]
)
def test_bad_date_is_reported(tmp_path, bad_date):
    path = write(
        tmp_path,
        "loans.csv",
        LOANS_HEADER + f"L001,M001,9780000000011,{bad_date},2026-10-20,\n",
    )
    with pytest.raises(ValidationError):
        load_loans(path)


def test_bad_paid_text_is_reported(tmp_path):
    path = write(tmp_path, "fines.csv", "loan_id,amount,paid\nL005,10,maybe\n")
    with pytest.raises(ValidationError):
        load_fines(path)


def test_missing_column_is_reported(tmp_path):
    path = write(tmp_path, "fines.csv", "loan_id,amount\nL005,10\n")
    with pytest.raises(ValidationError) as caught:
        load_fines(path)
    assert "paid" in caught.value.message


def test_duplicate_isbn_in_the_file_is_refused_and_nothing_is_stored(tmp_path):
    write_dataset(
        tmp_path,
        books="9780000000011,First,A,Cat,,Book,100,200,1\n"
        "9780000000011,Second,A,Cat,,Book,100,200,1\n",
    )
    items, members, loans, fines = fresh_repositories()
    with pytest.raises(ValidationError) as caught:
        load_data(tmp_path, items, members, loans, fines)
    assert "9780000000011" in caught.value.message
    assert items.count() == 0


def test_two_fines_for_the_same_loan_are_refused(tmp_path):
    write_dataset(tmp_path, fines="L001,10,no\nL001,20,no\n")
    with pytest.raises(ValidationError):
        load_data(tmp_path, *fresh_repositories())


# --- Every loan and fine must point at something real ------------------------


def test_loan_for_an_unknown_member_is_refused(tmp_path):
    write_dataset(
        tmp_path, loans="L001,M999,9780000000011,2026-09-01,2026-09-15,\n"
    )
    with pytest.raises(ValidationError) as caught:
        load_data(tmp_path, *fresh_repositories())
    assert "M999" in caught.value.message


def test_loan_for_an_unknown_isbn_is_refused(tmp_path):
    write_dataset(
        tmp_path, loans="L001,M001,9780000000999,2026-09-01,2026-09-15,\n"
    )
    with pytest.raises(ValidationError) as caught:
        load_data(tmp_path, *fresh_repositories())
    assert "9780000000999" in caught.value.message


def test_fine_for_an_unknown_loan_is_refused(tmp_path):
    write_dataset(tmp_path, fines="L999,10,no\n")
    with pytest.raises(ValidationError) as caught:
        load_data(tmp_path, *fresh_repositories())
    assert "L999" in caught.value.message


# --- All or nothing ----------------------------------------------------------


def test_a_broken_file_leaves_every_repository_empty(tmp_path):
    write_dataset(tmp_path, fines="L001,10,maybe\n")
    items, members, loans, fines = fresh_repositories()
    with pytest.raises(ValidationError):
        load_data(tmp_path, items, members, loans, fines)
    assert items.count() == 0
    assert members.count() == 0
    assert loans.list_all() == []
    assert fines.list_all() == []


# --- Reading the files safely ------------------------------------------------


def test_file_saved_with_a_bom_is_read(tmp_path):
    path = tmp_path / "fines.csv"
    path.write_bytes(b"\xef\xbb\xbf" + "loan_id,amount,paid\nL005,10,yes\n".encode())
    (fine,) = load_fines(path)
    assert fine.loan_id == "L005"


def test_file_that_is_not_utf8_gives_a_clear_error(tmp_path):
    path = tmp_path / "fines.csv"
    path.write_bytes(b"loan_id,amount,paid\nL005,10,\xff\n")
    with pytest.raises(ValidationError) as caught:
        load_fines(path)
    assert "UTF-8" in caught.value.message


def test_missing_file_gives_a_clear_error(tmp_path):
    with pytest.raises(ValidationError) as caught:
        load_items(tmp_path / "nothing.csv")
    assert "nothing.csv" in caught.value.message


# --- Loan numbering ----------------------------------------------------------


def test_loading_twice_still_leaves_l011_next():
    load_real_data()
    load_real_data()
    new_loan = Loan("M001", "9780000000011", date(2026, 10, 12), date(2026, 10, 26))
    assert new_loan.loan_id == "L011"