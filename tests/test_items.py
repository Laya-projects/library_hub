import pytest
from libraryhub.errors import InvalidISBNError, ItemNotBorrowableError
from libraryhub.items import Book, ItemType, LibraryItem, Magazine, ReferenceItem
from libraryhub.members import PremiumMember, RegularMember, StudentMember

WINGS_ISBN = "9780000000011"


def make_book(**overrides):
    details = {
        "isbn": WINGS_ISBN,
        "title": "Wings of Fire",
        "authors": ["A.P.J. Abdul Kalam", "Arun Tiwari"],
        "category": "Biography",
        "parent_category": None,
        "pages": 180,
        "price": 250,
        "total_copies": 2,
    }
    details.update(overrides)
    return Book(**details)


def make_magazine():
    return Magazine(
        isbn="9780000000073",
        title="India Today (Oct 2026)",
        authors=["Various"],
        category="Magazines",
        parent_category=None,
        pages=90,
        price=80,
        total_copies=3,
    )


def make_reference():
    return ReferenceItem(
        isbn="9780000000066",
        title="Encyclopaedia of Science",
        authors=["Various"],
        category="Reference",
        parent_category=None,
        pages=1200,
        price=2500,
        total_copies=1,
    )


def make_members():
    return [
        StudentMember("M001", "Asha Raman", "asha@example.com"),
        RegularMember("M002", "Rahul Mehta", "rahul@example.com"),
        PremiumMember("M003", "Sneha Iyer", "sneha@example.com"),
    ]


# --- R9: ISBN ---------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_isbn",
    [
        "123",
        "",
        "978000000001",  # 12 digits
        "97800000000111",  # 14 digits
        "97800000000ab",  # letters
        "978-000000001",  # dash
        " 9780000000011",  # leading space
        "٠٠٠٠٠٠٠٠٠٠٠٠٠",  # 13 digits from another script
    ],
)
def test_bad_isbn_is_rejected(bad_isbn):
    with pytest.raises(InvalidISBNError):
        make_book(isbn=bad_isbn)


def test_good_isbn_is_accepted():
    assert make_book().isbn == WINGS_ISBN


def test_changing_to_a_bad_isbn_raises_and_keeps_the_old_value():
    book = make_book()
    with pytest.raises(InvalidISBNError):
        book.isbn = "123"
    assert book.isbn == WINGS_ISBN


# --- Copies and title -------------------------------------------------------


def test_negative_copies_are_rejected():
    with pytest.raises(ValueError):
        make_book(total_copies=-1)


def test_zero_copies_are_allowed():
    assert make_book(total_copies=0).total_copies == 0


def test_changing_copies_to_negative_raises_and_keeps_the_old_value():
    book = make_book()
    with pytest.raises(ValueError):
        book.total_copies = -5
    assert book.total_copies == 2


@pytest.mark.parametrize("blank_title", ["", "   ", "\t\n"])
def test_blank_title_is_rejected(blank_title):
    with pytest.raises(ValueError):
        make_book(title=blank_title)


def test_title_is_stripped():
    assert make_book(title="  Wings of Fire ").title == "Wings of Fire"


# --- Abstract class and item types -----------------------------------------


def test_library_item_cannot_be_created_directly():
    with pytest.raises(TypeError):
        LibraryItem(WINGS_ISBN, "x", [], "c", None, 1, 1, 1)


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        (make_book(), ItemType.BOOK),
        (make_magazine(), ItemType.MAGAZINE),
        (make_reference(), ItemType.REFERENCE),
    ],
)
def test_item_type(item, expected):
    assert item.item_type() is expected


def test_authors_are_a_list_and_a_copy():
    authors = ["Eric Matthes"]
    book = make_book(authors=authors)
    authors.append("Someone Else")
    assert book.authors == ["Eric Matthes"]


# --- R1, R2, R6: how each kind of item is lent ------------------------------


def test_reference_item_is_not_borrowable():  # R1
    assert make_reference().is_borrowable() is False


def test_book_and_magazine_are_borrowable():
    assert make_book().is_borrowable() is True
    assert make_magazine().is_borrowable() is True


def test_reference_item_has_no_loan_period():
    with pytest.raises(ItemNotBorrowableError):
        make_reference().loan_period_for(make_members()[0])


@pytest.mark.parametrize("member", make_members(), ids=lambda m: m.membership_label())
def test_magazine_period_is_7_days_for_every_member(member):  # R2
    assert make_magazine().loan_period_for(member) == 7


@pytest.mark.parametrize(
    ("member", "days"),
    list(zip(make_members(), [14, 21, 30])),
)
def test_book_period_comes_from_the_member(member, days):
    assert make_book().loan_period_for(member) == days


@pytest.mark.parametrize(
    ("item", "renewals"),
    [(make_book(), 2), (make_magazine(), 0), (make_reference(), 0)],
)
def test_max_renewals(item, renewals):  # R2 and R6
    assert item.max_renewals() == renewals


# --- str and repr -----------------------------------------------------------


def test_str_reads_nicely():
    assert str(make_book()) == "Wings of Fire (Book, ISBN 9780000000011)"


def test_repr_shows_the_class_and_the_details():
    text = repr(make_reference())
    assert text.startswith("ReferenceItem(")
    assert "9780000000066" in text
    assert "Encyclopaedia of Science" in text