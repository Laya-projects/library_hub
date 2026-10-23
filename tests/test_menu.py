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


# --- Options 3 to 8 are not built yet -----------------------------------------


@pytest.mark.parametrize("choice", ["3", "4", "5", "6", "7", "8"])
def test_later_options_say_they_are_not_built_yet(library_world, choice):
    transcript = run_menu(library_world.library, [choice, "0"])
    assert transcript == [
        MENU_TEXT,
        "> " + choice,
        f"Option {choice} is not built yet.",
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