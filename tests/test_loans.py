from datetime import date

import pytest

from libraryhub.errors import ValidationError
from libraryhub.items import Book, Magazine
from libraryhub.loans import Fine, Loan
from libraryhub.members import PremiumMember, RegularMember, StudentMember

TODAY = date(2026, 10, 12)


@pytest.fixture(autouse=True)
def fresh_numbering():
    Loan.reset_numbering()


def student():
    return StudentMember("M004", "Karthik N", "karthik@example.com")


def regular():
    return RegularMember("M002", "Rahul Mehta", "rahul@example.com")


def book(isbn, title, price):
    return Book(isbn, title, ["Author"], "Fiction", None, 200, price, 1)


def magazine():
    return Magazine(
        "9780000000073", "India Today", ["Various"], "Magazines", None, 90, 80, 3
    )


def make_loan(due, return_date=None, loan_id="L001"):
    return Loan(
        "M001",
        "9780000000011",
        date(2026, 6, 1),
        due,
        loan_id=loan_id,
        return_date=return_date,
    )


# --- R10: days late ---------------------------------------------------------


@pytest.mark.parametrize(
    ("today", "expected"),
    [
        (date(2026, 9, 21), 0),  # before the due date
        (date(2026, 9, 22), 0),  # on the due date: not late
        (date(2026, 9, 23), 1),  # the day after: first late day
        (date(2026, 10, 12), 20),
    ],
)
def test_days_late(today, expected):
    assert make_loan(date(2026, 9, 22)).days_late(today) == expected


def test_lateness_stops_counting_when_the_item_is_returned():
    loan = make_loan(date(2026, 8, 3), return_date=date(2026, 8, 23))
    assert loan.days_late(TODAY) == 20


def test_is_overdue_only_while_the_item_is_out():
    open_loan = make_loan(date(2026, 9, 22))
    returned = make_loan(date(2026, 9, 22), return_date=date(2026, 9, 30))
    assert open_loan.is_overdue(TODAY) is True
    assert returned.is_overdue(TODAY) is False


def test_is_open():
    returned = make_loan(date(2026, 9, 22), return_date=date(2026, 9, 23))
    assert make_loan(date(2026, 9, 22)).is_open() is True
    assert returned.is_open() is False


# --- R5: fines --------------------------------------------------------------


def test_fine_is_days_late_times_the_daily_rate():
    # Rahul (Regular, Rs 5/day), due 2026-09-22, 20 days late
    alchemist = book("9780000000028", "The Alchemist", 300)
    assert make_loan(date(2026, 9, 22)).fine(TODAY, regular(), alchemist) == 100


def test_fine_for_a_student():
    # Karthik (Student, Rs 2/day), due 2026-10-05, 7 days late
    python_book = book("9780000000042", "Python Crash Course", 700)
    assert make_loan(date(2026, 10, 5)).fine(TODAY, student(), python_book) == 14


def test_fine_is_never_more_than_the_item_price():
    # 60 days late x Rs 2 = 120, but the magazine costs only Rs 80
    loan = make_loan(date(2026, 7, 8), return_date=date(2026, 9, 6))
    assert loan.fine(TODAY, student(), magazine()) == 80


def test_fine_for_a_returned_loan_does_not_grow():
    wings = book("9780000000011", "Wings of Fire", 250)
    loan = make_loan(date(2026, 8, 3), return_date=date(2026, 8, 23))
    assert loan.fine(TODAY, student(), wings) == 40


def test_no_fine_when_not_late():
    wings = book("9780000000011", "Wings of Fire", 250)
    assert make_loan(date(2026, 9, 22)).fine(date(2026, 9, 22), student(), wings) == 0


# --- Loan numbers -----------------------------------------------------------


def test_new_loans_get_the_next_number():
    first = Loan("M001", "9780000000011", TODAY, TODAY)
    second = Loan("M001", "9780000000028", TODAY, TODAY)
    assert (first.loan_id, second.loan_id) == ("L001", "L002")


def test_loaded_loans_move_the_counter_past_their_own_number():
    Loan("M001", "9780000000011", TODAY, TODAY, loan_id="L010")
    new_loan = Loan("M001", "9780000000028", TODAY, TODAY)
    assert new_loan.loan_id == "L011"


def test_reset_numbering_starts_again_from_one():
    Loan("M001", "9780000000011", TODAY, TODAY)
    Loan.reset_numbering()
    assert Loan("M001", "9780000000011", TODAY, TODAY).loan_id == "L001"


def test_loan_keeps_ids_and_dates():
    loan = Loan(
        "M004",
        "9780000000042",
        date(2026, 9, 21),
        date(2026, 10, 5),
        loan_id="L002",
    )
    assert loan.member_id == "M004"
    assert loan.isbn == "9780000000042"
    assert loan.renewals == 0
    assert loan.return_date is None


# --- Fine record ------------------------------------------------------------


def test_fine_holds_loan_id_amount_and_paid():
    fine = Fine("L009", 80)
    assert (fine.loan_id, fine.amount, fine.paid) == ("L009", 80, False)


def test_fine_can_be_marked_paid():
    fine = Fine("L009", 80)
    fine.paid = True
    assert str(fine) == "Fine for L009: ₹80 (paid)"


def test_fine_str_when_unpaid():
    assert str(Fine("L010", 40)) == "Fine for L010: ₹40 (unpaid)"


# --- str and repr -----------------------------------------------------------


def test_loan_str_reads_nicely():
    loan = make_loan(date(2026, 10, 5), loan_id="L002")
    assert str(loan) == "L002: M001 has 9780000000011, due 2026-10-05 (on loan)"


def test_loan_repr_shows_every_field():
    loan = make_loan(date(2026, 10, 5), return_date=date(2026, 10, 6), loan_id="L002")
    assert repr(loan) == (
        "Loan(loan_id='L002', member_id='M001', isbn='9780000000011', "
        "issue_date=2026-06-01, due_date=2026-10-05, return_date=2026-10-06, "
        "renewals=0)"
    )


# --- Renewing (R6) ----------------------------------------------------------


def test_renew_pushes_the_due_date_and_counts_the_renewal():
    sneha = PremiumMember("M003", "Sneha Iyer", "sneha@example.com")
    loan = Loan(
        "M003", "9780000000059", date(2026, 9, 20), date(2026, 10, 20), loan_id="L003"
    )
    loan.renew(sneha)
    assert (loan.due_date, loan.renewals) == (date(2026, 11, 19), 1)
    loan.renew(sneha)
    assert (loan.due_date, loan.renewals) == (date(2026, 12, 19), 2)


# --- A loan or fine that breaks a rule can never exist ---------------------


def test_due_date_before_issue_date_is_rejected():
    with pytest.raises(ValidationError):
        Loan("M001", "9780000000011", date(2026, 10, 12), date(2026, 10, 11))


def test_due_date_on_the_issue_date_is_allowed():
    assert Loan("M001", "9780000000011", TODAY, TODAY).due_date == TODAY


def test_negative_renewals_are_rejected():
    with pytest.raises(ValidationError):
        Loan("M001", "9780000000011", TODAY, TODAY, renewals=-1)


def test_negative_fine_amount_is_rejected():
    with pytest.raises(ValidationError):
        Fine("L009", -1)


def test_zero_fine_amount_is_allowed():
    assert Fine("L009", 0).amount == 0