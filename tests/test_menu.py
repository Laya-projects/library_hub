import inspect
from datetime import date

import pytest

from libraryhub import menu as menu_module
from libraryhub.errors import MemberNotFoundError
from libraryhub.menu import INVALID_CHOICE, MENU_TEXT, Menu

TODAY = date(2026, 10, 12)

CATALOGUE = """\
ISBN           TITLE                     TYPE       AVAILABLE
9780000000011  Wings of Fire             Book       2 of 2
9780000000028  The Alchemist             Book       0 of 1
9780000000035  Clean Code                Book       1 of 1
9780000000042  Python Crash Course       Book       1 of 2
9780000000059  Sapiens                   Book       0 of 1
9780000000066  Encyclopaedia of Science  Reference  not borrowable
9780000000073  India Today (Oct 2026)    Magazine   3 of 3"""


def run_menu(library, answers):
    """Run the menu with scripted answers and return the transcript.

    The fake input adds prompt + answer to the output, so the list reads like
    a real terminal session.
    """
    transcript = []
    remaining = iter(answers)

    def fake_input(prompt):
        try:
            answer = next(remaining)
        except StopIteration:
            raise AssertionError("The script ran out of answers") from None
        transcript.append(prompt + answer)
        return answer

    Menu(library, TODAY, fake_input, transcript.append).run()
    return transcript


# --- The loop ----------------------------------------------------------------


def test_zero_exits_and_the_menu_is_printed_once(library_world):
    transcript = run_menu(library_world.library, ["0"])
    assert transcript == [MENU_TEXT, "> 0"]  # nothing is printed after 0
    assert transcript.count(MENU_TEXT) == 1


def test_the_menu_is_not_printed_again_after_an_action(library_world):
    transcript = run_menu(library_world.library, ["abc", "1", "0"])
    assert transcript.count(MENU_TEXT) == 1


def test_menu_text_matches_the_brief():
    assert MENU_TEXT.splitlines() == [
        "=== LibraryHub Mini ===",
        "1. List catalogue",
        "2. Search by title or author",
        "3. Borrow",
        "4. Return",
        "5. Renew",
        "6. Join waiting list",
        "7. Member loans",
        "8. Overdue report",
        "0. Exit",
    ]


@pytest.mark.parametrize("bad", ["abc", "", "9", "-1", "1.5", "one", "01", "10"])
def test_invalid_choice_gives_the_error_and_the_loop_continues(library_world, bad):
    transcript = run_menu(library_world.library, [bad, "0"])
    assert transcript == [MENU_TEXT, "> " + bad, INVALID_CHOICE, "> 0"]


def test_invalid_choice_message_matches_the_brief():
    assert INVALID_CHOICE == "Please enter a number from 0 to 8."


def test_choices_are_stripped(library_world):
    transcript = run_menu(library_world.library, ["1 ", "  0"])
    assert transcript[2] == CATALOGUE
    assert transcript[-1] == ">   0"  # the typed spaces are echoed, then it exits


# --- Option 1 and 2 ----------------------------------------------------------


def test_option_1_lists_the_catalogue(library_world):
    transcript = run_menu(library_world.library, ["1", "0"])
    assert transcript == [MENU_TEXT, "> 1", CATALOGUE, "> 0"]


def test_option_2_finds_paulo(library_world):
    transcript = run_menu(library_world.library, ["2", "paulo", "0"])
    assert transcript == [
        MENU_TEXT,
        "> 2",
        "Search: paulo",
        "1 result:\n9780000000028  The Alchemist  (Paulo Coelho)  0 of 1",
        "> 0",
    ]


def test_option_2_finds_nothing_for_zzz(library_world):
    transcript = run_menu(library_world.library, ["2", "zzz", "0"])
    assert transcript[2:4] == ["Search: zzz", "No items match 'zzz'."]


def test_search_text_is_stripped(library_world):
    transcript = run_menu(library_world.library, ["2", "  paulo  ", "0"])
    assert transcript[3].startswith("1 result:")


def test_a_blank_search_prints_the_error_and_the_menu_goes_on(library_world):
    transcript = run_menu(library_world.library, ["2", "", "0"])
    assert transcript[2:5] == [
        "Search: ",
        "ERROR [ValidationError]: Search text cannot be blank.",
        "> 0",
    ]


# --- Option 3: borrow -----------------------------------------------------------

ALCHEMIST_ISBN = "9780000000028"  # 0 of 1 available
WINGS_ISBN = "9780000000011"
MAGAZINE_ISBN = "9780000000073"
REFERENCE_ISBN = "9780000000066"


def test_option_3_borrows_a_book(library_world):
    transcript = run_menu(library_world.library, ["3", "M001", WINGS_ISBN, "0"])
    assert transcript[1:] == [
        "> 3",
        "Member ID: M001",
        "ISBN: " + WINGS_ISBN,
        "OK: Asha Raman borrowed 'Wings of Fire'. Due 2026-10-26.",
        "> 0",
    ]


def test_option_3_unknown_member_is_reported_before_the_isbn_is_asked(library_world):
    transcript = run_menu(library_world.library, ["3", "M999", "0"])
    assert transcript[1:] == [
        "> 3",
        "Member ID: M999",
        "ERROR [MemberNotFoundError]: No member with ID M999.",
        "> 0",
    ]


def test_option_3_bad_isbn(library_world):
    transcript = run_menu(library_world.library, ["3", "M001", "123", "0"])
    assert transcript[4] == "ERROR [InvalidISBNError]: ISBN must be exactly 13 digits."


def test_option_3_reference_item_is_r1(library_world):
    transcript = run_menu(library_world.library, ["3", "M001", REFERENCE_ISBN, "0"])
    assert transcript[4].startswith("ERROR [R1]:")


def test_option_3_unavailable_then_yes_joins_the_waiting_list(library_world):
    transcript = run_menu(library_world.library, ["3", "M001", ALCHEMIST_ISBN, "y", "0"])
    assert transcript[4:6] == [
        ("No copies of 'The Alchemist' are available. "
        "Join the waiting list? (y/n): y"),
        "OK: Asha Raman is #1 on the waiting list for 'The Alchemist'.",
    ]


def test_option_3_unavailable_then_no_prints_nothing_more(library_world):
    transcript = run_menu(library_world.library, ["3", "M001", ALCHEMIST_ISBN, "n", "0"])
    assert transcript[4:] == [
        ("No copies of 'The Alchemist' are available. "
        "Join the waiting list? (y/n): n"),
        "> 0",
    ]


def test_option_3_any_answer_but_y_means_no(library_world):
    transcript = run_menu(library_world.library, ["3", "M001", ALCHEMIST_ISBN, "maybe", "0"])
    assert transcript[-1] == "> 0"
    assert transcript[-2].endswith("maybe")  # no OK line in between


def test_option_3_capital_y_and_spaces_still_mean_yes(library_world):
    transcript = run_menu(library_world.library, ["3", "M001", ALCHEMIST_ISBN, " Y ", "0"])
    assert transcript[5].startswith("OK: Asha Raman is #1")


# --- Option 4: return ---------------------------------------------------------------


def test_option_4_returns_a_late_loan_with_its_fine(library_world):
    transcript = run_menu(library_world.library, ["4", "L001", "0"])
    assert transcript[1:] == [
        "> 4",
        "Loan ID: L001",
        "OK: Rahul Mehta returned 'The Alchemist'. Late by 20 days. Fine: ₹100.",
        "> 0",
    ]


def test_option_4_names_the_next_member_on_the_waiting_list(library_world):
    transcript = run_menu(
        library_world.library,
        ["6", "M001", ALCHEMIST_ISBN, "4", "L001", "0"],
    )
    assert transcript[-2].endswith(
        "Fine: ₹100.\nNext on waiting list: Asha Raman."
    )


def test_option_4_the_same_loan_twice_is_an_error(library_world):
    transcript = run_menu(library_world.library, ["4", "L001", "4", "L001", "0"])
    assert transcript[-2].startswith("ERROR [LoanAlreadyReturnedError]: Loan L001")


def test_option_4_unknown_loan(library_world):
    transcript = run_menu(library_world.library, ["4", "L999", "0"])
    assert transcript[3] == "ERROR [LoanNotFoundError]: No loan with ID L999."


# --- Option 5: renew ----------------------------------------------------------------


def _borrow(library_world, member_id, isbn):
    return library_world.library.borrow(member_id, isbn, TODAY)


def test_option_5_renews_a_book(library_world):
    loan = _borrow(library_world, "M001", WINGS_ISBN)
    transcript = run_menu(library_world.library, ["5", loan.loan_id, "0"])
    assert transcript[3] == (
        "OK: Renewed 'Wings of Fire' (renewal 1 of 2). New due date 2026-11-09."
    )


def test_option_5_magazines_cannot_be_renewed(library_world):
    loan = _borrow(library_world, "M001", MAGAZINE_ISBN)
    transcript = run_menu(library_world.library, ["5", loan.loan_id, "0"])
    assert transcript[3] == "ERROR [R2]: Magazines cannot be renewed."


def test_option_5_unknown_loan(library_world):
    transcript = run_menu(library_world.library, ["5", "L999", "0"])
    assert transcript[3] == "ERROR [LoanNotFoundError]: No loan with ID L999."


# --- Option 6: join the waiting list ---------------------------------------------------


def test_option_6_joins_the_waiting_list(library_world):
    transcript = run_menu(library_world.library, ["6", "M001", ALCHEMIST_ISBN, "0"])
    assert transcript[1:] == [
        "> 6",
        "Member ID: M001",
        "ISBN: " + ALCHEMIST_ISBN,
        "OK: Asha Raman is #1 on the waiting list for 'The Alchemist'.",
        "> 0",
    ]


def test_option_6_second_member_is_number_two(library_world):
    transcript = run_menu(
        library_world.library,
        ["6", "M001", ALCHEMIST_ISBN, "6", "M003", ALCHEMIST_ISBN, "0"],
    )
    assert transcript[-2].endswith("is #2 on the waiting list for 'The Alchemist'.")


def test_option_6_the_same_member_twice_is_an_error(library_world):
    transcript = run_menu(
        library_world.library,
        ["6", "M001", ALCHEMIST_ISBN, "6", "M001", ALCHEMIST_ISBN, "0"],
    )
    assert "already on the waiting list" in transcript[-2]


def test_option_6_when_a_copy_is_free_says_to_borrow(library_world):
    transcript = run_menu(library_world.library, ["6", "M001", WINGS_ISBN, "0"])
    assert "Borrow it instead." in transcript[4]


def test_option_6_unknown_member_is_reported_before_the_isbn(library_world):
    transcript = run_menu(library_world.library, ["6", "M999", "0"])
    assert transcript[3] == "ERROR [MemberNotFoundError]: No member with ID M999."


# --- Options 7 and 8: reports ------------------------------------------------------------


def test_option_7_member_loans_matches_the_brief(library_world):
    transcript = run_menu(library_world.library, ["7", "M002", "0"])
    assert transcript[1:] == [
        "> 7",
        "Member ID: M002",
        ("Loans for Rahul Mehta (Regular: 5 items, 21 days, ₹5/day)\n"
        "LOAN  TITLE          ISSUED      DUE         STATUS\n"
        "L001  The Alchemist  2026-09-01  2026-09-22  OVERDUE (20 days)\n"
        "Active loans: 1 of 5\n"
        "Unpaid fines: ₹0"),
        "> 0",
    ]


def test_option_7_unknown_member(library_world):
    transcript = run_menu(library_world.library, ["7", "M999", "0"])
    assert transcript[3] == "ERROR [MemberNotFoundError]: No member with ID M999."


def test_option_8_overdue_report_matches_the_brief(library_world):
    transcript = run_menu(library_world.library, ["8", "0"])
    assert transcript[1:] == [
        "> 8",
        ("Overdue loans as of 2026-10-12\n"
        "LOAN  MEMBER       TITLE                DUE         DAYS  FINE SO FAR\n"
        "L001  Rahul Mehta  The Alchemist        2026-09-22    20  ₹100\n"
        "L002  Karthik N    Python Crash Course  2026-10-05     7  ₹14\n"
        "Total overdue: 2   Fines so far: ₹114"),
        "> 0",
    ]


# --- Errors and leaving cleanly -------------------------------------------------


class LibraryThatRaises:
    """A stand-in whose catalogue call fails with a LibraryError."""

    def list_items(self):
        raise MemberNotFoundError("M009")


def test_a_library_error_prints_its_formatted_line_and_the_loop_continues():
    transcript = run_menu(LibraryThatRaises(), ["1", "0"])
    assert transcript == [
        MENU_TEXT,
        "> 1",
        "ERROR [MemberNotFoundError]: No member with ID M009.",
        "> 0",
    ]


@pytest.mark.parametrize("exit_error", [EOFError, KeyboardInterrupt])
def test_end_of_input_or_ctrl_c_ends_cleanly(library_world, exit_error):
    output = []

    def input_that_ends(prompt):
        raise exit_error

    Menu(library_world.library, TODAY, input_that_ends, output.append).run()
    assert output == [MENU_TEXT]  # printed once, then a clean exit


@pytest.mark.parametrize(
    "answers",
    [["3"], ["3", "M001"], ["3", "M001", ALCHEMIST_ISBN], ["4"], ["5"], ["6", "M001"], ["7"]],
)
def test_end_of_input_in_the_middle_of_any_flow_ends_cleanly(library_world, answers):
    output = []
    remaining = iter(answers)

    def input_that_ends(prompt):
        try:
            return next(remaining)
        except StopIteration:
            raise EOFError from None

    Menu(library_world.library, TODAY, input_that_ends, output.append).run()
    assert output[0] == MENU_TEXT


def test_end_of_input_in_the_middle_of_an_action_ends_cleanly(library_world):
    output = []
    answers = iter(["2"])

    def input_that_ends_after_choice(prompt):
        try:
            return next(answers)
        except StopIteration:
            raise EOFError from None

    menu = Menu(
        library_world.library, TODAY, input_that_ends_after_choice, output.append
    )
    menu.run()
    assert output == [MENU_TEXT]  # the Search prompt hit the end of input


def test_the_menu_can_run_again_after_it_has_ended(library_world):
    first = run_menu(library_world.library, ["0"])
    second = run_menu(library_world.library, ["0"])
    assert first == second == [MENU_TEXT, "> 0"]


# --- No rule logic in the menu ----------------------------------------------------


def test_actions_are_looked_up_in_a_dictionary(library_world):
    menu = Menu(library_world.library, TODAY, input, print)
    assert sorted(menu._actions) == ["0", "1", "2", "3", "4", "5", "6", "7", "8"]


def test_menu_uses_the_library_and_not_the_rules():
    source = inspect.getsource(menu_module)
    assert "calculations" not in source
    assert "csv" not in source