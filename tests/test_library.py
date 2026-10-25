import copy
import inspect
import logging
import re
from datetime import date, datetime

import pytest

from libraryhub import library as library_module
from libraryhub.errors import (
    BorrowLimitExceededError,
    DuplicateLoanError,
    InvalidISBNError,
    ItemNotAvailableError,
    ItemNotBorrowableError,
    ItemNotFoundError,
    LoanAlreadyReturnedError,
    LoanNotFoundError,
    MemberNotFoundError,
    RenewalNotAllowedError,
    UnpaidFinesError,
    ValidationError,
)
from libraryhub.library import Library
from libraryhub.loans import Fine, Loan
from libraryhub.repositories import InMemoryLoanRepository

TODAY = date(2026, 10, 12)

WINGS = "9780000000011"
ALCHEMIST = "9780000000028"
CLEAN_CODE = "9780000000035"
PYTHON_BOOK = "9780000000042"
SAPIENS = "9780000000059"
ENCYCLOPAEDIA = "9780000000066"
INDIA_TODAY = "9780000000073"

ASHA, RAHUL, SNEHA, KARTHIK, DIVYA = "M001", "M002", "M003", "M004", "M005"


class CopyingLoanRepository(InMemoryLoanRepository):
    """Behaves like a database: it hands out copies of loans.

    A change to a copy is lost unless Library calls update().
    """

    def get(self, loan_id):
        loan = super().get(loan_id)
        return None if loan is None else copy.copy(loan)

    def list_all(self):
        return [copy.copy(loan) for loan in super().list_all()]

    def list_open(self):
        return [copy.copy(loan) for loan in super().list_open()]

    def list_for_member(self, member_id):
        return [copy.copy(loan) for loan in super().list_for_member(member_id)]

    def list_for_isbn(self, isbn):
        return [copy.copy(loan) for loan in super().list_for_isbn(isbn)]


def test_a1_asha_borrows_wings_of_fire(world):
    loan = world.library.borrow(ASHA, WINGS, TODAY)
    assert loan.loan_id == "L011"
    assert loan.due_date == date(2026, 10, 26)
    assert loan.is_open()
    assert world.library.available_copies(WINGS) == 1


def test_a2_asha_cannot_borrow_the_same_title_twice(world):  # R8
    world.library.borrow(ASHA, WINGS, TODAY)
    with pytest.raises(DuplicateLoanError) as caught:
        world.library.borrow(ASHA, WINGS, TODAY)
    assert caught.value.formatted() == (
        "ERROR [R8]: Asha Raman already has a copy of 'Wings of Fire'."
    )


def test_a3_reference_items_cannot_be_borrowed(world):  # R1
    with pytest.raises(ItemNotBorrowableError) as caught:
        world.library.borrow(SNEHA, ENCYCLOPAEDIA, TODAY)
    assert caught.value.formatted() == (
        "ERROR [R1]: 'Encyclopaedia of Science' is a reference item "
        "and cannot be borrowed."
    )


def test_a4_karthik_is_blocked_by_unpaid_fines(world):  # R4
    with pytest.raises(UnpaidFinesError) as caught:
        world.library.borrow(KARTHIK, CLEAN_CODE, TODAY)
    assert caught.value.formatted() == (
        "ERROR [R4]: Karthik N has unpaid fines of ₹120 (limit ₹100)."
    )


def test_a5_sneha_joins_the_waiting_list_for_the_alchemist(world):  # R7
    with pytest.raises(ItemNotAvailableError) as caught:
        world.library.borrow(SNEHA, ALCHEMIST, TODAY)
    assert caught.value.message == "No copies of 'The Alchemist' are available."
    assert world.library.reserve(SNEHA, ALCHEMIST) == 1


def test_a6_rahul_returns_the_alchemist_and_sneha_is_next(world):  # R5, R10
    world.library.reserve(SNEHA, ALCHEMIST)
    result = world.library.return_item("L001", TODAY)
    assert result.member.name == "Rahul Mehta"
    assert result.item.title == "The Alchemist"
    assert result.days_late == 20
    assert result.fine == 100
    assert result.next_waiting.name == "Sneha Iyer"


def test_a7_rahul_owes_exactly_100_and_can_still_borrow(world):  # R4
    world.library.return_item("L001", TODAY)
    assert world.library.unpaid_fines_for(RAHUL) == 100
    loan = world.library.borrow(RAHUL, WINGS, TODAY)
    assert loan.is_open()


# --- Other error paths --------------------------------------------------------


def test_unknown_member(world):
    with pytest.raises(MemberNotFoundError) as caught:
        world.library.borrow("M009", WINGS, TODAY)
    assert caught.value.formatted() == (
        "ERROR [MemberNotFoundError]: No member with ID M009."
    )


def test_invalid_isbn_is_not_the_same_as_unknown_isbn(world):  # R9
    with pytest.raises(InvalidISBNError) as caught:
        world.library.borrow(ASHA, "123", TODAY)
    assert caught.value.formatted() == (
        "ERROR [InvalidISBNError]: ISBN must be exactly 13 digits."
    )
    with pytest.raises(ItemNotFoundError) as caught:
        world.library.borrow(ASHA, "9780000000999", TODAY)
    assert caught.value.formatted() == (
        "ERROR [ItemNotFoundError]: No item with ISBN 9780000000999."
    )


def test_student_cannot_have_more_than_three_items(world):  # R3
    for isbn in (WINGS, CLEAN_CODE, INDIA_TODAY):
        world.library.borrow(ASHA, isbn, TODAY)
    with pytest.raises(BorrowLimitExceededError) as caught:
        world.library.borrow(ASHA, PYTHON_BOOK, TODAY)
    assert caught.value.formatted() == (
        "ERROR [R3]: Asha Raman already has 3 of 3 items on loan."
    )


def test_a_loan_that_is_not_known_is_reported(world):
    with pytest.raises(LoanNotFoundError) as caught:
        world.library.return_item("L999", TODAY)
    assert caught.value.formatted() == (
        "ERROR [LoanNotFoundError]: No loan with ID L999."
    )
    with pytest.raises(LoanNotFoundError):
        world.library.renew("L999", TODAY)


def test_a_returned_loan_cannot_be_returned_or_renewed_again(world):
    with pytest.raises(LoanAlreadyReturnedError) as caught:
        world.library.return_item("L004", TODAY)
    assert caught.value.formatted() == (
        "ERROR [LoanAlreadyReturnedError]: Loan L004 was already returned "
        "on 2026-09-24."
    )
    with pytest.raises(LoanAlreadyReturnedError):
        world.library.renew("L004", TODAY)


def test_returning_twice_in_a_row_is_refused(world):
    world.library.return_item("L001", TODAY)
    with pytest.raises(LoanAlreadyReturnedError):
        world.library.return_item("L001", TODAY)
    assert len(world.fines.list_all()) == 5  # the fine was stored only once


# --- Worked examples through the Library ------------------------------------


@pytest.mark.parametrize(
    ("member_id", "isbn", "due"),
    [
        (ASHA, WINGS, date(2026, 10, 26)),  # Student, Book: 14 days
        (RAHUL, WINGS, date(2026, 11, 2)),  # Regular, Book: 21 days
        (SNEHA, WINGS, date(2026, 11, 11)),  # Premium, Book: 30 days
        (SNEHA, INDIA_TODAY, date(2026, 10, 19)),  # Premium, Magazine: 7 days (R2)
    ],
)
def test_due_date_worked_examples(world, member_id, isbn, due):
    assert world.library.borrow(member_id, isbn, TODAY).due_date == due


# --- Returns and fines (R5, R10) ----------------------------------------------


def test_returning_on_time_costs_nothing_and_stores_no_fine(world):  # R10
    result = world.library.return_item("L003", TODAY)
    assert (result.days_late, result.fine) == (0, 0)
    assert len(world.fines.list_all()) == 4


def test_returning_on_the_due_date_is_not_late(world):  # R10
    result = world.library.return_item("L002", date(2026, 10, 5))
    assert (result.days_late, result.fine) == (0, 0)


def test_returning_one_day_late_costs_one_days_rate(world):  # R5, R10
    result = world.library.return_item("L002", date(2026, 10, 6))
    assert (result.days_late, result.fine) == (1, 2)


def test_a_late_return_stores_an_unpaid_fine(world):
    world.library.return_item("L001", TODAY)
    stored = [fine for fine in world.fines.list_all() if fine.loan_id == "L001"]
    assert [(fine.amount, fine.paid) for fine in stored] == [(100, False)]


def test_the_fine_is_capped_at_the_price(world):  # R5
    loan = world.library.borrow(ASHA, INDIA_TODAY, TODAY)  # due 2026-10-19
    result = world.library.return_item(loan.loan_id, date(2026, 12, 18))
    assert result.days_late == 60
    assert result.fine == 80  # 60 x 2 = 120, but the magazine costs 80


def test_returning_sets_the_return_date_and_frees_the_copy(world):
    world.library.return_item("L001", TODAY)
    assert world.library.get_loan("L001").return_date == TODAY
    assert world.library.available_copies(ALCHEMIST) == 1


# --- Renewing (R2, R6) --------------------------------------------------------


def test_renewal_one_of_two(world):
    result = world.library.renew("L003", TODAY)
    assert (result.renewal_number, result.max_renewals) == (1, 2)
    assert result.new_due_date == date(2026, 11, 19)


def test_renewal_two_of_two(world):
    world.library.renew("L003", TODAY)
    result = world.library.renew("L003", TODAY)
    assert (result.renewal_number, result.max_renewals) == (2, 2)
    assert result.new_due_date == date(2026, 12, 19)


def test_a_third_renewal_is_refused(world):  # R6
    world.library.renew("L003", TODAY)
    world.library.renew("L003", TODAY)
    with pytest.raises(RenewalNotAllowedError) as caught:
        world.library.renew("L003", TODAY)
    assert caught.value.formatted() == (
        "ERROR [R6]: 'Sapiens' has already been renewed 2 times."
    )


def test_magazines_cannot_be_renewed(world):  # R2
    loan = world.library.borrow(SNEHA, INDIA_TODAY, TODAY)
    with pytest.raises(RenewalNotAllowedError) as caught:
        world.library.renew(loan.loan_id, TODAY)
    assert caught.value.formatted() == "ERROR [R2]: Magazines cannot be renewed."


def test_no_renewal_while_someone_is_waiting(world):  # R6
    world.library.reserve(ASHA, SAPIENS)
    with pytest.raises(RenewalNotAllowedError) as caught:
        world.library.renew("L003", TODAY)
    assert caught.value.formatted() == (
        "ERROR [R6]: 'Sapiens' cannot be renewed because another member "
        "is waiting."
    )


def test_a_refused_renewal_changes_nothing(world):
    world.library.reserve(ASHA, SAPIENS)
    with pytest.raises(RenewalNotAllowedError):
        world.library.renew("L003", TODAY)
    loan = world.library.get_loan("L003")
    assert (loan.due_date, loan.renewals) == (date(2026, 10, 20), 0)


# --- The waiting list (R7) ------------------------------------------------------


def test_positions_follow_the_order_of_joining(world):
    assert world.library.reserve(SNEHA, ALCHEMIST) == 1
    assert world.library.reserve(DIVYA, ALCHEMIST) == 2


def test_the_first_in_line_is_served_first(world):
    world.library.reserve(SNEHA, ALCHEMIST)
    world.library.reserve(DIVYA, ALCHEMIST)
    world.library.return_item("L001", TODAY)
    with pytest.raises(ItemNotAvailableError):
        world.library.borrow(DIVYA, ALCHEMIST, TODAY)  # second in line
    assert world.library.borrow(SNEHA, ALCHEMIST, TODAY).is_open()


def test_a_free_copy_is_held_for_the_waiting_list(world):
    world.library.reserve(SNEHA, ALCHEMIST)
    world.library.return_item("L001", TODAY)
    with pytest.raises(ItemNotAvailableError):
        world.library.borrow(DIVYA, ALCHEMIST, TODAY)  # not in the queue at all


def test_a_member_who_borrows_leaves_the_waiting_list(world):
    world.library.reserve(SNEHA, ALCHEMIST)
    world.library.return_item("L001", TODAY)
    loan = world.library.borrow(SNEHA, ALCHEMIST, TODAY)
    world.library.return_item(loan.loan_id, TODAY)
    # nobody is waiting any more, so Divya can borrow it
    assert world.library.borrow(DIVYA, ALCHEMIST, TODAY).is_open()


def test_extra_free_copies_are_not_held_back(world):
    # Wings of Fire has 2 copies and nobody is waiting
    assert world.library.borrow(ASHA, WINGS, TODAY).is_open()
    assert world.library.borrow(RAHUL, WINGS, TODAY).is_open()


def test_two_queued_members_are_served_in_order_and_others_are_refused(world):
    library = world.library
    library.reserve(SNEHA, ALCHEMIST)  # #1
    library.reserve(ASHA, ALCHEMIST)  # #2
    library.return_item("L001", TODAY)  # the only copy comes back
    with pytest.raises(ItemNotAvailableError):
        library.borrow(RAHUL, ALCHEMIST, TODAY)  # not queued: behind both
    assert library.borrow(SNEHA, ALCHEMIST, TODAY).is_open()  # first in line
    with pytest.raises(ItemNotAvailableError):
        library.borrow(ASHA, ALCHEMIST, TODAY)  # next in line, but no copy left


def test_cannot_join_the_list_twice(world):
    world.library.reserve(SNEHA, ALCHEMIST)
    with pytest.raises(ValidationError):
        world.library.reserve(SNEHA, ALCHEMIST)


def test_cannot_join_the_list_while_a_copy_is_free(world):
    with pytest.raises(ValidationError) as caught:
        world.library.reserve(ASHA, WINGS)
    assert "available" in caught.value.message


def test_cannot_join_the_list_for_a_title_already_held(world):
    with pytest.raises(DuplicateLoanError):
        world.library.reserve(RAHUL, ALCHEMIST)  # Rahul holds it (L001)


def test_cannot_join_the_list_for_a_reference_item(world):
    with pytest.raises(ItemNotBorrowableError):
        world.library.reserve(ASHA, ENCYCLOPAEDIA)


# --- The order of the checks ------------------------------------------------------


def give_karthik_two_more_loans(world):
    world.loans.add(Loan(KARTHIK, WINGS, TODAY, date(2026, 10, 26)))
    world.loans.add(Loan(KARTHIK, CLEAN_CODE, TODAY, date(2026, 10, 26)))


def test_member_who_breaks_r4_and_r3_together_gets_r4(world):
    give_karthik_two_more_loans(world)  # 3 of 3 items, and 120 in unpaid fines
    with pytest.raises(UnpaidFinesError):
        world.library.borrow(KARTHIK, SAPIENS, TODAY)


def test_once_the_fines_are_paid_the_same_member_gets_r3(world):
    give_karthik_two_more_loans(world)
    for fine in world.fines.list_all():
        fine.paid = True
    with pytest.raises(BorrowLimitExceededError):
        world.library.borrow(KARTHIK, SAPIENS, TODAY)


def test_r1_comes_before_r4(world):
    with pytest.raises(ItemNotBorrowableError):
        world.library.borrow(KARTHIK, ENCYCLOPAEDIA, TODAY)  # also owes 120


def test_r3_comes_before_r8(world):
    for isbn in (WINGS, CLEAN_CODE, INDIA_TODAY):
        world.library.borrow(ASHA, isbn, TODAY)
    with pytest.raises(BorrowLimitExceededError):
        world.library.borrow(ASHA, WINGS, TODAY)  # also already holds it


def test_r8_comes_before_availability(world):
    with pytest.raises(DuplicateLoanError):
        world.library.borrow(RAHUL, ALCHEMIST, TODAY)  # holds it, and 0 are free


def test_unknown_member_is_checked_before_the_isbn(world):
    with pytest.raises(MemberNotFoundError):
        world.library.borrow("M009", "123", TODAY)


# --- Looking things up ------------------------------------------------------------


def test_available_copies_are_rebuilt_from_open_loans(world):
    library = world.library
    assert library.available_copies(WINGS) == 2
    assert library.available_copies(ALCHEMIST) == 0
    assert library.available_copies(PYTHON_BOOK) == 1
    assert library.available_copies(SAPIENS) == 0
    assert library.available_copies(INDIA_TODAY) == 3


def test_available_copies_check_the_isbn(world):
    with pytest.raises(InvalidISBNError):
        world.library.available_copies("123")
    with pytest.raises(ItemNotFoundError):
        world.library.available_copies("9780000000999")


def test_unpaid_fines_for_each_member(world):
    library = world.library
    assert library.unpaid_fines_for(KARTHIK) == 120
    assert library.unpaid_fines_for(RAHUL) == 0
    assert library.unpaid_fines_for(ASHA) == 0


def test_list_items_returns_all_seven(world):
    assert len(world.library.list_items()) == 7


# --- Changes reach the repository through update() ---------------------------------


def test_a_return_is_saved_even_when_the_repository_hands_out_copies(make_world):
    world = make_world(CopyingLoanRepository())
    world.library.return_item("L001", TODAY)
    assert world.loans.get("L001").return_date == TODAY
    assert world.library.available_copies(ALCHEMIST) == 1


def test_a_renewal_is_saved_even_when_the_repository_hands_out_copies(make_world):
    world = make_world(CopyingLoanRepository())
    world.library.renew("L003", TODAY)
    saved = world.loans.get("L003")
    assert (saved.due_date, saved.renewals) == (date(2026, 11, 19), 1)


def test_a_new_loan_is_stored_by_borrow(make_world):
    world = make_world(CopyingLoanRepository())
    loan = world.library.borrow(ASHA, WINGS, TODAY)
    assert world.loans.get(loan.loan_id).member_id == ASHA


# --- Reports ------------------------------------------------------------------------


def test_member_loans_for_rahul(world):
    report = world.library.member_loans(RAHUL, TODAY)
    assert report.member.name == "Rahul Mehta"
    assert [line.loan.loan_id for line in report.lines] == ["L001"]
    assert report.lines[0].item.title == "The Alchemist"
    assert report.lines[0].days_late == 20
    assert report.unpaid_fines == 0


def test_member_loans_show_a_loan_that_is_not_overdue_with_zero_days(world):
    report = world.library.member_loans(SNEHA, TODAY)
    assert [(line.loan.loan_id, line.days_late) for line in report.lines] == [
        ("L003", 0)
    ]


def test_member_loans_for_an_unknown_member(world):
    with pytest.raises(MemberNotFoundError):
        world.library.member_loans("M009", TODAY)


def test_overdue_report_is_sorted_most_late_first(world):
    report = world.library.overdue_report(TODAY)
    assert [
        (line.loan.loan_id, line.member.name, line.days_late, line.fine_so_far)
        for line in report
    ] == [
        ("L001", "Rahul Mehta", 20, 100),
        ("L002", "Karthik N", 7, 14),
    ]
    assert sum(line.fine_so_far for line in report) == 114


def test_overdue_report_is_empty_when_nothing_is_late(world):
    assert world.library.overdue_report(date(2026, 9, 1)) == []


# --- The Library never reads files or the clock and never prints -----------------


def test_library_has_no_file_access_clock_or_printing():
    source = inspect.getsource(library_module)
    # \b so that loan.is_open() is not mistaken for a call to open()
    forbidden = [r"\bopen\(", r"import csv", r"today\(\)", r"now\(\)", r"\bprint\("]
    for pattern in forbidden:
        assert re.search(pattern, source) is None


# --- Step 7: Audit trail, generator, reports, logging ------------------------


def test_audit_preserves_method_name():
    assert Library.borrow.__name__ == "borrow"
    assert Library.return_item.__name__ == "return_item"
    assert Library.renew.__name__ == "renew"


def test_successful_borrow_adds_exactly_one_entry_with_fixed_clock(world):
    fixed_time = datetime(2026, 10, 12, 10, 0, 0)
    world.library.audit_log.clock = lambda: fixed_time

    assert len(world.library.audit_log) == 0
    loan = world.library.borrow(ASHA, WINGS, TODAY)

    assert len(world.library.audit_log) == 1
    entry = world.library.audit_log.entries[0]
    assert entry.time == fixed_time
    assert entry.action == "borrow"
    assert entry.member_id == ASHA
    assert entry.isbn == WINGS
    assert entry.member_id == loan.member_id


def test_refused_borrow_adds_no_audit_entry(world):
    fixed_time = datetime(2026, 10, 12, 10, 0, 0)
    world.library.audit_log.clock = lambda: fixed_time

    # R1: Reference item is not borrowable
    with pytest.raises(ItemNotBorrowableError):
        world.library.borrow(ASHA, ENCYCLOPAEDIA, TODAY)

    assert len(world.library.audit_log) == 0


def test_successful_return_and_renew_add_audit_entries(world):
    fixed_time = datetime(2026, 10, 12, 11, 0, 0)
    world.library.audit_log.clock = lambda: fixed_time

    # Return L001
    ret = world.library.return_item("L001", TODAY)
    assert len(world.library.audit_log) == 1
    assert world.library.audit_log.entries[0].action == "return"
    assert world.library.audit_log.entries[0].member_id == ret.member.member_id
    assert world.library.audit_log.entries[0].isbn == ret.item.isbn

    # Renew L003
    ren = world.library.renew("L003", TODAY)
    assert len(world.library.audit_log) == 2
    assert world.library.audit_log.entries[1].action == "renew"
    assert world.library.audit_log.entries[1].member_id == ren.loan.member_id
    assert world.library.audit_log.entries[1].isbn == ren.item.isbn


def test_iter_overdue_is_lazy(world):
    gen = world.library.iter_overdue(TODAY)
    assert inspect.isgenerator(gen)

    # Lazily fetch the first overdue line without processing all loans
    first = next(gen)
    assert first.loan.loan_id == "L001"
    assert first.days_late == 20
    assert first.fine_so_far == 100

    second = next(gen)
    assert second.loan.loan_id == "L002"
    assert second.days_late == 7
    assert second.fine_so_far == 14

    with pytest.raises(StopIteration):
        next(gen)


def test_overdue_report_still_matches_brief(world):
    report = world.library.overdue_report(TODAY)
    assert [
        (line.loan.loan_id, line.days_late, line.fine_so_far) for line in report
    ] == [
        ("L001", 20, 100),
        ("L002", 7, 14),
    ]


def test_items_by_category_report_on_starter_data(world):
    report = world.library.items_by_category()
    assert report == {
        "Biography": ["Wings of Fire"],
        "Fiction": ["The Alchemist"],
        "History": ["Sapiens"],
        "Magazines": ["India Today (Oct 2026)"],
        "Programming": ["Python Crash Course"],
        "Reference": ["Encyclopaedia of Science"],
        "Software Engineering": ["Clean Code"],
    }
    # Also verify alias
    assert world.library.category_report() == report


def test_members_with_unpaid_fines_on_starter_data(world):
    report = world.library.members_with_unpaid_fines()
    assert len(report) == 1
    line = report[0]
    assert line.member.name == "Karthik N"
    assert line.amount == 120
    # Also verify unpacking and properties
    member, amt = line
    assert member.name == "Karthik N"
    assert amt == 120
    assert line.fine == 120
    assert line.unpaid == 120
    # Also verify alias
    assert world.library.unpaid_fines_report() == report


def test_members_with_unpaid_fines_sorting_largest_first_ties_by_name(world):
    # Add a fine for Rahul Mehta (M002) of 120 so both Karthik and Rahul owe 120
    world.fines.add(Fine("L007", 120, paid=False))
    # Ties by name: "Karthik N" comes before "Rahul Mehta"
    report = world.library.members_with_unpaid_fines()
    assert [(line.member.name, line.amount) for line in report] == [
        ("Karthik N", 120),
        ("Rahul Mehta", 120),
    ]


def test_logging_successful_and_refused_operations(world, caplog):
    caplog.set_level(logging.INFO, logger="libraryhub.library")

    # Successful borrow logs INFO
    world.library.borrow(ASHA, WINGS, TODAY)
    assert any(
        rec.levelno == logging.INFO and "Borrow successful" in rec.getMessage()
        for rec in caplog.records
    )

    # Refused borrow logs WARNING
    with pytest.raises(ItemNotBorrowableError):
        world.library.borrow(ASHA, ENCYCLOPAEDIA, TODAY)
    assert any(
        rec.levelno == logging.WARNING and "Borrow refused" in rec.getMessage()
        for rec in caplog.records
    )

    # Successful return logs INFO
    world.library.return_item("L001", TODAY)
    assert any(
        rec.levelno == logging.INFO and "Return successful" in rec.getMessage()
        for rec in caplog.records
    )

    # Refused return logs WARNING
    with pytest.raises(LoanAlreadyReturnedError):
        world.library.return_item("L001", TODAY)
    assert any(
        rec.levelno == logging.WARNING and "Return refused" in rec.getMessage()
        for rec in caplog.records
    )

    # Successful renew logs INFO
    world.library.renew("L003", TODAY)
    assert any(
        rec.levelno == logging.INFO and "Renewal successful" in rec.getMessage()
        for rec in caplog.records
    )

    # Refused renew logs WARNING (magazines cannot be renewed R2)
    # L009 is a magazine
    with pytest.raises(LoanAlreadyReturnedError):
        world.library.renew("L009", TODAY)
    assert any(
        rec.levelno == logging.WARNING and "Renewal refused" in rec.getMessage()
        for rec in caplog.records
    )


def test_unexpected_bug_propagates_unlabelled_without_warning_log(world, caplog):
    caplog.set_level(logging.WARNING, logger="libraryhub.library")

    # Simulate an unexpected bug (e.g. KeyError) during borrow check
    def buggy_check(member, item):
        raise KeyError("corrupt_data")

    world.library._borrow_checks = lambda: [buggy_check]

    with pytest.raises(KeyError, match="corrupt_data"):
        world.library.borrow(ASHA, WINGS, TODAY)

    assert not any("Borrow refused" in rec.getMessage() for rec in caplog.records)


# --- Step 8.2: searching the catalogue -----------------------------------------


@pytest.mark.parametrize("text", ["paulo", "PAULO", "Paulo", "  paulo  "])
def test_search_finds_the_alchemist_whatever_the_case(world, text):
    titles = [item.title for item in world.library.search_items(text)]
    assert titles == ["The Alchemist"]


def test_search_matches_the_second_author(world):
    titles = [item.title for item in world.library.search_items("tiwari")]
    assert titles == ["Wings of Fire"]


def test_search_includes_reference_items_in_catalogue_order(world):
    titles = [item.title for item in world.library.search_items("various")]
    assert titles == ["Encyclopaedia of Science", "India Today (Oct 2026)"]


def test_search_matches_a_piece_of_the_title(world):
    titles = [item.title for item in world.library.search_items("crash")]
    assert titles == ["Python Crash Course"]


def test_search_with_no_match_returns_an_empty_list(world):
    assert world.library.search_items("zzz") == []


def test_search_results_keep_catalogue_order(world):
    isbns = [item.isbn for item in world.library.search_items("a")]
    catalogue = [item.isbn for item in world.library.list_items()]
    assert isbns == [isbn for isbn in catalogue if isbn in isbns]
    assert len(isbns) > 2


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_a_blank_search_is_refused(world, blank):
    with pytest.raises(ValidationError) as caught:
        world.library.search_items(blank)
    assert caught.value.formatted() == (
        "ERROR [ValidationError]: Search text cannot be blank."
    )

def test_waiting_list_is_first_come_first_served(library_world):
    library = library_world.library
    library.reserve("M005", ALCHEMIST)
    library.reserve("M001", ALCHEMIST)
    assert [m.member_id for m in library.waiting_list(ALCHEMIST)] == ["M005", "M001"]


def test_return_names_the_first_and_lists_the_rest(library_world):
    library = library_world.library
    library.reserve("M005", ALCHEMIST)
    library.reserve("M001", ALCHEMIST)
    result = library.return_item("L001", TODAY)
    assert result.next_waiting.member_id == "M005"
    assert [m.member_id for m in result.still_waiting] == ["M001"]


def test_the_second_in_line_cannot_jump_the_queue(library_world):
    library = library_world.library
    library.reserve("M005", ALCHEMIST)
    library.reserve("M001", ALCHEMIST)
    library.return_item("L001", TODAY)
    with pytest.raises(ItemNotAvailableError):
        library.borrow("M001", ALCHEMIST, TODAY)  # second in line, one free copy
    library.borrow("M005", ALCHEMIST, TODAY)  # first in line gets it
    assert [m.member_id for m in library.waiting_list(ALCHEMIST)] == ["M001"]