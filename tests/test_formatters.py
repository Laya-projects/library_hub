from datetime import date
from types import SimpleNamespace

from libraryhub.formatters import (
    format_borrowed,
    format_catalogue,
    format_days,
    format_member_loans,
    format_money,
    format_overdue_report,
    format_renewed,
    format_returned,
    format_search_results,
    format_table,
    format_waiting_joined,
    format_waiting_list,
)
from libraryhub.items import Book
from libraryhub.library import LoanLine, MemberLoans
from libraryhub.loans import Loan
from libraryhub.members import RegularMember, StudentMember

TODAY = date(2026, 10, 12)


def _no_trailing_spaces(text: str) -> bool:
    return all(line == line.rstrip(" ") for line in text.splitlines())


# --- Money and day helpers ----------------------------------------------------


def test_format_money():
    assert format_money(0) == "₹0"
    assert format_money(100) == "₹100"
    assert format_money(300) == "₹300"


def test_format_days_is_singular_for_one():
    assert format_days(1) == "1 day"
    assert format_days(0) == "0 days"
    assert format_days(20) == "20 days"


# --- Table helper -------------------------------------------------------------


def test_table_with_one_row():
    headers = ["ID", "NAME"]
    rows = [["1", "Alice"]]
    expected = "ID  NAME\n1   Alice"
    assert format_table(headers, rows) == expected


def test_table_widths_follow_data_and_titles():
    headers = ["ID", "TITLE"]
    rows = [
        ["1", "Short"],
        ["2", "A Much Longer Book Title Here"],
    ]
    expected = (
        "ID  TITLE\n"
        "1   Short\n"
        "2   A Much Longer Book Title Here"
    )
    result = format_table(headers, rows)
    assert result == expected
    assert _no_trailing_spaces(result), "Lines must not have trailing spaces"


def test_table_right_alignment():
    headers = ["ITEM", "COUNT"]
    rows = [
        ["Book", "100"],
        ["Magazine", "5"],
    ]
    # COUNT is right-aligned
    expected = (
        "ITEM      COUNT\n"
        "Book        100\n"
        "Magazine      5"
    )
    result = format_table(headers, rows, right_aligned=["COUNT"])
    assert result == expected
    assert _no_trailing_spaces(result)


def test_table_without_rows_is_just_the_header():
    assert format_table(["ID", "NAME"], []) == "ID  NAME"


# --- Option 1: Catalogue formatter --------------------------------------------


def test_catalogue_formatter_matches_brief_sample(library_world):
    items = library_world.library.list_items()
    # Each entry is (item, copies available now)
    rows = [
        (item, library_world.library.available_copies(item.isbn))
        for item in items
    ]
    expected = (
        "ISBN           TITLE                     TYPE       AVAILABLE\n"
        "9780000000011  Wings of Fire             Book       2 of 2\n"
        "9780000000028  The Alchemist             Book       0 of 1\n"
        "9780000000035  Clean Code                Book       1 of 1\n"
        "9780000000042  Python Crash Course       Book       1 of 2\n"
        "9780000000059  Sapiens                   Book       0 of 1\n"
        "9780000000066  Encyclopaedia of Science  Reference  not borrowable\n"
        "9780000000073  India Today (Oct 2026)    Magazine   3 of 3"
    )
    result = format_catalogue(rows)
    assert result == expected
    assert _no_trailing_spaces(result)


# --- Option 2: Search results formatter ---------------------------------------


def test_search_results_single_match(library_world):
    item = library_world.library.get_item("9780000000028")
    avail = library_world.library.available_copies(item.isbn)
    expected = (
        "1 result:\n"
        "9780000000028  The Alchemist  (Paulo Coelho)  0 of 1"
    )
    assert format_search_results("paulo", [(item, avail)]) == expected


def test_search_results_multiple_matches_and_author_joining():
    b1 = Book(
        "9780000000011",
        "Wings of Fire",
        ["A.P.J. Abdul Kalam", "Arun Tiwari"],
        "Biography",
        None,
        180,
        250,
        2,
    )
    b2 = Book(
        "9780000000042",
        "Python Crash Course",
        ["Eric Matthes"],
        "Programming",
        None,
        544,
        700,
        2,
    )
    expected = (
        "2 results:\n"
        "9780000000011  Wings of Fire  (A.P.J. Abdul Kalam, Arun Tiwari)  2 of 2\n"
        "9780000000042  Python Crash Course  (Eric Matthes)  1 of 2"
    )
    assert format_search_results("Book", [(b1, 2), (b2, 1)]) == expected


def test_search_results_no_matches():
    assert format_search_results("zzz", []) == "No items match 'zzz'."


# --- Option 7: Member loans formatter -----------------------------------------


def test_member_loans_formatter_matches_brief_sample(library_world):
    # Rahul Mehta (M002) has 1 loan L001 that is 20 days late on 2026-10-12
    report = library_world.library.member_loans("M002", TODAY)
    expected = (
        "Loans for Rahul Mehta (Regular: 5 items, 21 days, ₹5/day)\n"
        "LOAN  TITLE          ISSUED      DUE         STATUS\n"
        "L001  The Alchemist  2026-09-01  2026-09-22  OVERDUE (20 days)\n"
        "Active loans: 1 of 5\n"
        "Unpaid fines: ₹0"
    )
    result = format_member_loans(report)
    assert result == expected
    assert _no_trailing_spaces(result)


def test_member_loans_no_active_loans():
    member = RegularMember("M005", "Divya Rao", "divya@example.com")
    report = MemberLoans(member, [], 0)
    expected = (
        "Loans for Divya Rao (Regular: 5 items, 21 days, ₹5/day)\n"
        "No active loans.\n"
        "Active loans: 0 of 5\n"
        "Unpaid fines: ₹0"
    )
    assert format_member_loans(report) == expected


def test_member_loans_not_overdue_shows_on_loan():
    member = StudentMember("M001", "Asha Raman", "asha@example.com")
    book = Book("9780000000011", "Wings", ["Author"], "Bio", None, 100, 100, 1)
    loan = Loan(
        "M001",
        "9780000000011",
        date(2026, 10, 12),
        date(2026, 10, 26),
        loan_id="L011",
    )
    report = MemberLoans(member, [LoanLine(loan, book, 0)], 0)
    expected = (
        "Loans for Asha Raman (Student: 3 items, 14 days, ₹2/day)\n"
        "LOAN  TITLE  ISSUED      DUE         STATUS\n"
        "L011  Wings  2026-10-12  2026-10-26  On loan\n"
        "Active loans: 1 of 3\n"
        "Unpaid fines: ₹0"
    )
    assert format_member_loans(report) == expected


def test_member_loans_singular_overdue_day():
    member = StudentMember("M001", "Asha Raman", "asha@example.com")
    book = Book("9780000000011", "Wings", ["Author"], "Bio", None, 100, 100, 1)
    loan = Loan(
        "M001",
        "9780000000011",
        date(2026, 9, 1),
        date(2026, 9, 15),
        loan_id="L001",
    )
    report = MemberLoans(member, [LoanLine(loan, book, 1)], 0)
    result = format_member_loans(report)
    assert "OVERDUE (1 day)" in result
    assert "1 days" not in result


# --- Option 8: Overdue report formatter ---------------------------------------


def test_overdue_report_formatter_matches_brief_sample(library_world):
    report = library_world.library.overdue_report(TODAY)
    expected = (
        "Overdue loans as of 2026-10-12\n"
        "LOAN  MEMBER       TITLE                DUE         DAYS  FINE SO FAR\n"
        "L001  Rahul Mehta  The Alchemist        2026-09-22    20  ₹100\n"
        "L002  Karthik N    Python Crash Course  2026-10-05     7  ₹14\n"
        "Total overdue: 2   Fines so far: ₹114"
    )
    result = format_overdue_report(report, TODAY)
    assert result == expected
    assert _no_trailing_spaces(result)


def test_overdue_report_empty():
    expected = (
        "Overdue loans as of 2026-09-01\n"
        "No overdue loans.\n"
        "Total overdue: 0   Fines so far: ₹0"
    )
    assert format_overdue_report([], date(2026, 9, 1)) == expected


# --- Result messages for options 3 to 6 ---------------------------------------

ASHA = SimpleNamespace(name="Asha Raman")
ALCHEMIST = SimpleNamespace(title="The Alchemist")


def _returned(days_late, fine, next_waiting=None, still_waiting=()):
    return SimpleNamespace(
        member=SimpleNamespace(name="Rahul Mehta"),
        item=ALCHEMIST,
        days_late=days_late,
        fine=fine,
        next_waiting=next_waiting,
        still_waiting=still_waiting,
    )


def test_returned_lists_who_is_still_waiting():
    sneha = SimpleNamespace(name="Sneha Iyer")
    text = format_returned(_returned(20, 100, next_waiting=sneha, still_waiting=(ASHA,)))
    assert text.splitlines()[-2:] == [
        "Next on waiting list: Sneha Iyer.",
        "Waiting list for 'The Alchemist': Asha Raman",
    ]


def test_waiting_list_line_names_everyone_in_order():
    assert format_waiting_list(ALCHEMIST, [SimpleNamespace(name="Sneha Iyer"), ASHA]) == (
        "Waiting list for 'The Alchemist': Sneha Iyer, Asha Raman"
    )


def test_borrowed_message():
    item = SimpleNamespace(title="Wings of Fire")
    loan = SimpleNamespace(due_date=date(2026, 10, 26))
    assert format_borrowed(ASHA, item, loan) == (
        "OK: Asha Raman borrowed 'Wings of Fire'. Due 2026-10-26."
    )


def test_returned_late_message():
    assert format_returned(_returned(20, 100)) == (
        "OK: Rahul Mehta returned 'The Alchemist'. Late by 20 days. Fine: ₹100."
    )


def test_returned_one_day_late_is_singular():
    text = format_returned(_returned(1, 5))
    assert "Late by 1 day." in text
    assert "1 days" not in text


def test_returned_on_time_message():
    assert format_returned(_returned(0, 0)) == (
        "OK: Rahul Mehta returned 'The Alchemist'. Returned on time. Fine: ₹0."
    )


def test_returned_names_the_next_member_on_the_waiting_list():
    text = format_returned(_returned(0, 0, next_waiting=ASHA))
    assert text.splitlines()[-1] == "Next on waiting list: Asha Raman."
    assert len(text.splitlines()) == 2


def test_renewed_message():
    result = SimpleNamespace(
        item=SimpleNamespace(title="Sapiens"),
        renewal_number=1,
        max_renewals=2,
        new_due_date=date(2026, 11, 19),
    )
    assert format_renewed(result) == (
        "OK: Renewed 'Sapiens' (renewal 1 of 2). New due date 2026-11-19."
    )


def test_waiting_joined_message():
    assert format_waiting_joined(ASHA, ALCHEMIST, 1) == (
        "OK: Asha Raman is #1 on the waiting list for 'The Alchemist'."
    )