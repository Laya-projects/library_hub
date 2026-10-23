from datetime import date

import pytest

from libraryhub.errors import LoanNotFoundError, ValidationError
from libraryhub.items import Book
from libraryhub.loans import Fine, Loan
from libraryhub.members import RegularMember, StudentMember
from libraryhub.repositories import (
    FineRepository,
    InMemoryFineRepository,
    InMemoryItemRepository,
    InMemoryLoanRepository,
    InMemoryMemberRepository,
    ItemRepository,
    LoanRepository,
    MemberRepository,
)

DAY = date(2026, 10, 12)


@pytest.fixture(autouse=True)
def fresh_numbering():
    Loan.reset_numbering()


def make_book(isbn="9780000000011", title="Wings of Fire"):
    return Book(isbn, title, ["Author"], "Biography", None, 180, 250, 2)


def make_member(member_id="M001", name="Asha Raman"):
    return StudentMember(member_id, name, "asha@example.com")


def make_loan(loan_id, member_id="M001", isbn="9780000000011", returned=None):
    return Loan(
        member_id, isbn, DAY, DAY, loan_id=loan_id, return_date=returned
    )


# --- The interfaces cannot be used directly ---------------------------------


@pytest.mark.parametrize(
    "interface",
    [ItemRepository, MemberRepository, LoanRepository, FineRepository],
)
def test_interfaces_cannot_be_created(interface):
    with pytest.raises(TypeError):
        interface()


# --- Items ------------------------------------------------------------------


def test_add_and_get_an_item():
    items = InMemoryItemRepository()
    book = make_book()
    items.add(book)
    assert items.get("9780000000011") is book


def test_get_returns_none_when_the_item_is_missing():
    assert InMemoryItemRepository().get("9780000000999") is None


def test_second_item_with_the_same_isbn_is_refused():  # R9
    items = InMemoryItemRepository()
    first = make_book(title="First")
    items.add(first)
    with pytest.raises(ValidationError) as caught:
        items.add(make_book(title="Second"))
    assert caught.value.field == "isbn"
    assert items.count() == 1
    assert items.get("9780000000011") is first


def test_item_count_and_list_all():
    items = InMemoryItemRepository()
    assert items.count() == 0
    items.add(make_book("9780000000011", "A"))
    items.add(make_book("9780000000028", "B"))
    assert items.count() == 2
    assert [item.title for item in items.list_all()] == ["A", "B"]


def test_changing_the_returned_list_does_not_change_the_repository():
    items = InMemoryItemRepository()
    items.add(make_book())
    items.list_all().clear()
    assert items.count() == 1


def test_the_objects_inside_are_shared_on_purpose():
    items = InMemoryItemRepository()
    items.add(make_book())
    items.list_all()[0].total_copies = 7  # Library must be able to change objects
    assert items.get("9780000000011").total_copies == 7


def test_each_repository_starts_empty():
    first, second = InMemoryItemRepository(), InMemoryItemRepository()
    first.add(make_book())
    assert second.count() == 0


# --- Members ----------------------------------------------------------------


def test_add_and_get_a_member():
    members = InMemoryMemberRepository()
    asha = make_member()
    members.add(asha)
    assert members.get("M001") is asha
    assert members.count() == 1


def test_get_returns_none_when_the_member_is_missing():
    assert InMemoryMemberRepository().get("M009") is None


def test_second_member_with_the_same_id_is_refused():
    members = InMemoryMemberRepository()
    members.add(make_member())
    with pytest.raises(ValidationError):
        members.add(RegularMember("M001", "Someone Else", "else@example.com"))
    assert members.count() == 1


def test_member_list_all():
    members = InMemoryMemberRepository()
    members.add(make_member("M001", "Asha Raman"))
    members.add(make_member("M002", "Rahul Mehta"))
    assert [member.name for member in members.list_all()] == [
        "Asha Raman",
        "Rahul Mehta",
    ]


# --- Loans ------------------------------------------------------------------


def test_add_and_get_a_loan():
    loans = InMemoryLoanRepository()
    loan = make_loan("L001")
    loans.add(loan)
    assert loans.get("L001") is loan


def test_get_returns_none_when_the_loan_is_missing():
    assert InMemoryLoanRepository().get("L999") is None


def test_second_loan_with_the_same_id_is_refused():
    loans = InMemoryLoanRepository()
    loans.add(make_loan("L001"))
    with pytest.raises(ValidationError):
        loans.add(make_loan("L001", member_id="M002"))
    assert len(loans.list_all()) == 1


def test_update_replaces_the_stored_loan():
    loans = InMemoryLoanRepository()
    loans.add(make_loan("L001"))
    replacement = make_loan("L001", returned=DAY)
    loans.update(replacement)
    assert loans.get("L001") is replacement
    assert len(loans.list_all()) == 1


def test_update_keeps_the_place_in_the_list():
    loans = InMemoryLoanRepository()
    for loan_id in ["L001", "L002", "L003"]:
        loans.add(make_loan(loan_id))
    loans.update(make_loan("L002", returned=DAY))
    assert [loan.loan_id for loan in loans.list_all()] == ["L001", "L002", "L003"]
    assert [loan.loan_id for loan in loans.list_open()] == ["L001", "L003"]


def test_update_of_an_unknown_loan_is_refused():
    loans = InMemoryLoanRepository()
    with pytest.raises(LoanNotFoundError):
        loans.update(make_loan("L999"))


def test_list_open_leaves_out_returned_loans():
    loans = InMemoryLoanRepository()
    loans.add(make_loan("L001"))
    loans.add(make_loan("L002", returned=DAY))
    loans.add(make_loan("L003"))
    assert [loan.loan_id for loan in loans.list_open()] == ["L001", "L003"]


def test_list_for_member_and_for_isbn():
    loans = InMemoryLoanRepository()
    loans.add(make_loan("L001", "M001", "9780000000011"))
    loans.add(make_loan("L002", "M002", "9780000000011"))
    loans.add(make_loan("L003", "M001", "9780000000028"))
    assert [loan.loan_id for loan in loans.list_for_member("M001")] == ["L001", "L003"]
    assert [loan.loan_id for loan in loans.list_for_isbn("9780000000011")] == [
        "L001",
        "L002",
    ]
    assert loans.list_for_member("M009") == []
    assert loans.list_for_isbn("9780000000999") == []


def test_loans_keep_the_order_they_were_added():
    loans = InMemoryLoanRepository()
    for loan_id in ["L003", "L001", "L002"]:
        loans.add(make_loan(loan_id))
    assert [loan.loan_id for loan in loans.list_all()] == ["L003", "L001", "L002"]


# --- Fines ------------------------------------------------------------------


def test_add_and_list_fines():
    fines = InMemoryFineRepository()
    assert fines.list_all() == []
    fines.add(Fine("L009", 80))
    fines.add(Fine("L010", 40, paid=True))
    assert [(fine.loan_id, fine.amount) for fine in fines.list_all()] == [
        ("L009", 80),
        ("L010", 40),
    ]


def test_second_fine_for_the_same_loan_is_refused():
    fines = InMemoryFineRepository()
    fines.add(Fine("L009", 80))
    with pytest.raises(ValidationError):
        fines.add(Fine("L009", 10))
    assert len(fines.list_all()) == 1


def test_a_fine_can_be_marked_paid_through_the_repository():
    fines = InMemoryFineRepository()
    fines.add(Fine("L009", 80))
    fines.list_all()[0].paid = True
    assert fines.list_all()[0].paid is True


def test_fine_list_is_a_copy():
    fines = InMemoryFineRepository()
    fines.add(Fine("L009", 80))
    fines.list_all().clear()
    assert len(fines.list_all()) == 1