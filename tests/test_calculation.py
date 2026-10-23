import inspect
from datetime import date

import pytest

from libraryhub import calculations
from libraryhub.calculations import (
    days_late,
    due_date,
    exceeds_fine_limit,
    fine_amount,
    renewed_due_date,
    unpaid_total,
)
from libraryhub.items import Book, Magazine
from libraryhub.loans import Fine, Loan
from libraryhub.members import PremiumMember, RegularMember, StudentMember

TODAY = date(2026, 10, 12)


def member_of(kind):
    return kind("M001", "Asha Raman", "asha@example.com")


def item_of(kind, price=250):
    return kind(
        "9780000000011", "Some Title", ["Author"], "Fiction", None, 100, price, 1
    )


# --- Worked examples: due dates (R2) ----------------------------------------


@pytest.mark.parametrize(
    ("member_kind", "item_kind", "expected"),
    [
        (StudentMember, Book, date(2026, 10, 26)),
        (RegularMember, Book, date(2026, 11, 2)),
        (PremiumMember, Book, date(2026, 11, 11)),
        (PremiumMember, Magazine, date(2026, 10, 19)),  # R2: 7 days whatever the member
    ],
)
def test_due_date_worked_examples(member_kind, item_kind, expected):
    result = due_date(TODAY, item_of(item_kind), member_of(member_kind))
    assert result == expected


# --- Days late (R10) --------------------------------------------------------


@pytest.mark.parametrize(
    ("due", "today", "returned", "expected"),
    [
        (date(2026, 10, 5), date(2026, 10, 4), None, 0),  # not due yet
        (date(2026, 10, 5), date(2026, 10, 5), None, 0),  # the due date is not late
        (date(2026, 10, 5), date(2026, 10, 6), None, 1),  # first late day
        (date(2026, 9, 22), date(2026, 10, 12), None, 20),  # L001 still open
        (date(2026, 7, 8), date(2026, 10, 12), date(2026, 9, 6), 60),  # L009
        (date(2026, 7, 8), date(2027, 1, 1), date(2026, 9, 6), 60),  # any "today"
        (date(2026, 10, 5), date(2026, 10, 12), date(2026, 10, 1), 0),  # early return
    ],
)
def test_days_late(due, today, returned, expected):
    assert days_late(due, today, returned) == expected


# --- Worked examples: fines (R5, R10) ---------------------------------------


@pytest.mark.parametrize(
    ("member_kind", "item_kind", "price", "due", "returned", "late", "fine"),
    [
        (StudentMember, Book, 250, date(2026, 10, 5), date(2026, 10, 5), 0, 0),  # R10
        (StudentMember, Book, 250, date(2026, 10, 5), date(2026, 10, 6), 1, 2),
        (RegularMember, Book, 300, date(2026, 9, 22), date(2026, 10, 12), 20, 100),
        (PremiumMember, Book, 600, date(2026, 9, 1), date(2026, 10, 1), 30, 90),
        (StudentMember, Magazine, 80, date(2026, 7, 8), date(2026, 9, 6), 60, 80),
    ],
)
def test_fine_worked_examples(
    member_kind, item_kind, price, due, returned, late, fine
):
    days = days_late(due, TODAY, returned)
    rate = member_of(member_kind).fine_per_day()
    assert days == late
    assert fine_amount(days, rate, price) == fine


def test_fine_is_capped_at_the_price():
    assert fine_amount(60, 2, 80) == 80
    assert fine_amount(40, 2, 80) == 80  # exactly the price
    assert fine_amount(39, 2, 80) == 78


# --- Renewing (R6) ----------------------------------------------------------


def test_renewing_adds_the_members_loan_period_each_time():
    sneha = PremiumMember("M003", "Sneha Iyer", "sneha@example.com")
    first = renewed_due_date(date(2026, 10, 20), sneha)
    second = renewed_due_date(first, sneha)
    assert first == date(2026, 11, 19)
    assert second == date(2026, 12, 19)


@pytest.mark.parametrize(
    ("member_kind", "expected"),
    [
        (StudentMember, date(2026, 11, 3)),
        (RegularMember, date(2026, 11, 10)),
        (PremiumMember, date(2026, 11, 19)),
    ],
)
def test_renewal_length_depends_on_the_member(member_kind, expected):
    assert renewed_due_date(date(2026, 10, 20), member_of(member_kind)) == expected


# --- R4: the fine limit -----------------------------------------------------


@pytest.mark.parametrize(
    ("unpaid", "blocked"),
    [(0, False), (99, False), (100, False), (101, True), (120, True)],
)
def test_exceeds_fine_limit(unpaid, blocked):
    assert exceeds_fine_limit(unpaid) is blocked


def test_exceeds_fine_limit_accepts_another_limit():
    assert exceeds_fine_limit(60, limit=50) is True
    assert exceeds_fine_limit(50, limit=50) is False


# --- Unpaid total (D1) with the starter data --------------------------------

# loan_id, member_id, isbn, issue date, due date, return date (from loans.csv)
STARTER_LOANS = [
    ("L001", "M002", "9780000000028", (2026, 9, 1), (2026, 9, 22), None),
    ("L002", "M004", "9780000000042", (2026, 9, 21), (2026, 10, 5), None),
    ("L003", "M003", "9780000000059", (2026, 9, 20), (2026, 10, 20), None),
    ("L004", "M001", "9780000000011", (2026, 9, 10), (2026, 9, 24), (2026, 9, 24)),
    ("L005", "M001", "9780000000042", (2026, 8, 1), (2026, 8, 15), (2026, 8, 20)),
    ("L006", "M003", "9780000000035", (2026, 8, 5), (2026, 9, 4), (2026, 9, 2)),
    ("L007", "M002", "9780000000042", (2026, 7, 10), (2026, 7, 31), (2026, 7, 31)),
    ("L008", "M002", "9780000000011", (2026, 6, 1), (2026, 6, 22), (2026, 6, 30)),
    ("L009", "M004", "9780000000073", (2026, 7, 1), (2026, 7, 8), (2026, 9, 6)),
    ("L010", "M004", "9780000000011", (2026, 7, 20), (2026, 8, 3), (2026, 8, 23)),
]
# loan_id, amount, paid (from fines.csv)
STARTER_FINES = [
    ("L005", 10, True),
    ("L008", 40, True),
    ("L009", 80, False),
    ("L010", 40, False),
]


def starter_loans():
    return [
        Loan(
            member,
            isbn,
            date(*issued),
            date(*due),
            loan_id=loan_id,
            return_date=None if back is None else date(*back),
        )
        for loan_id, member, isbn, issued, due, back in STARTER_LOANS
    ]


def starter_fines():
    return [Fine(loan_id, amount, paid) for loan_id, amount, paid in STARTER_FINES]


@pytest.mark.parametrize(
    ("member_id", "expected"),
    [
        ("M001", 0),  # only a paid fine
        ("M002", 0),  # Rahul: L001 is overdue, but its ₹100 is not a stored fine yet
        ("M003", 0),
        ("M004", 120),  # Karthik: 80 + 40
        ("M005", 0),  # never borrowed
        ("M999", 0),  # not a member at all
    ],
)
def test_unpaid_total_with_the_starter_data(member_id, expected):
    assert unpaid_total(member_id, starter_fines(), starter_loans()) == expected


def test_karthiks_total_is_over_the_limit_and_rahuls_is_not():
    loans, fines = starter_loans(), starter_fines()
    assert exceeds_fine_limit(unpaid_total("M004", fines, loans)) is True
    assert exceeds_fine_limit(unpaid_total("M002", fines, loans)) is False


def test_paying_a_fine_lowers_the_total():
    loans, fines = starter_loans(), starter_fines()
    fines[3].paid = True  # Karthik pays L010
    assert unpaid_total("M004", fines, loans) == 80


def test_a_fine_for_an_unknown_loan_is_an_error_not_silence():
    with pytest.raises(KeyError):
        unpaid_total("M004", [Fine("L999", 50)], starter_loans())


# --- Purity -----------------------------------------------------------------


def test_calculations_never_read_the_clock():
    source = inspect.getsource(calculations)
    assert "today()" not in source
    assert "now()" not in source