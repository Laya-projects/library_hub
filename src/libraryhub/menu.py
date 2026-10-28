"""The console menu. It reads choices and prints; it holds no rule logic.

Every rule lives in `Library`. The menu asks the Library, then prints what
comes back or the formatted error. Input and output are injected so a test can
script the whole conversation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from libraryhub.errors import ItemNotAvailableError, LibraryError
from libraryhub.formatters import (
    format_borrowed,
    format_catalogue,
    format_member_loans,
    format_overdue_report,
    format_renewed,
    format_returned,
    format_search_results,
    format_undone,
    format_waiting_joined,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import date

    from libraryhub.items import LibraryItem
    from libraryhub.library import Library
    from libraryhub.members import Member

MENU_TEXT = """=== LibraryHub Mini ===
1. List catalogue
2. Search by title or author
3. Borrow
4. Return
5. Renew
6. Join waiting list
7. Member loans
8. Overdue report
9. Undo last borrow/return
0. Exit"""

PROMPT = "> "
INVALID_CHOICE = "Please enter a number from 0 to 9."
JOIN_QUESTION = "Join the waiting list? (y/n): "


class Menu:
    def __init__(
        self,
        library: Library,
        today: date,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> None:
        self._library = library
        self._today = today
        self._input = input_fn
        self._output = output_fn
        self._running = False
        # Dictionary dispatch: a choice is a key, so there is no if-chain.
        self._actions: dict[str, Callable[[], None]] = {
            "1": self._list_catalogue,
            "2": self._search,
            "3": self._borrow,
            "4": self._return_item,
            "5": self._renew,
            "6": self._join_waiting_list,
            "7": self._member_loans,
            "8": self._overdue_report,
            "9": self._undo,
            "0": self._exit,
        }

    # --- The loop ---------------------------------------------------------------

    def run(self) -> None:
        """Print the menu once, then read choices until 0, end of input or Ctrl+C."""
        self._output(MENU_TEXT)
        self._running = True
        try:
            while self._running:
                self._handle(self._ask(PROMPT))
        except (EOFError, KeyboardInterrupt):
            pass  # Ctrl+Z, Ctrl+C or a script that ended: leave quietly
        finally:
            self._running = False

    def _ask(self, prompt: str) -> str:
        """The only place that reads input, so stripping happens once."""
        return self._input(prompt).strip()

    def _handle(self, choice: str) -> None:
        action = self._actions.get(choice)
        if action is None:
            self._output(INVALID_CHOICE)
            return
        try:
            action()
        except LibraryError as error:
            self._output(error.formatted())  # the only place that shows an error

    # --- Small helpers ------------------------------------------------------------

    def _ask_member(self) -> Member:
        """Ask for a member ID and look the member up straight away.

        An unknown member is reported before the ISBN or loan is ever asked.
        """
        return self._library.get_member(self._ask("Member ID: "))

    def _with_availability(
        self, items: list[LibraryItem]
    ) -> list[tuple[LibraryItem, int]]:
        """Pair each item with the copies available now, for the formatters."""
        return [(item, self._library.available_copies(item.isbn)) for item in items]

    # --- Options 1 and 2: browsing --------------------------------------------------

    def _list_catalogue(self) -> None:
        entries = self._with_availability(self._library.list_items())
        self._output(format_catalogue(entries))

    def _search(self) -> None:
        text = self._ask("Search: ")
        entries = self._with_availability(self._library.search_items(text))
        self._output(format_search_results(text, entries))

    # --- Option 3: borrow, with the waiting-list question ------------------------------

    def _borrow(self) -> None:
        member = self._ask_member()
        isbn = self._ask("ISBN: ")
        try:
            loan = self._library.borrow(member.member_id, isbn, self._today)
        except ItemNotAvailableError as error:
            # The message and the question share one line, as in the brief.
            answer = self._ask(f"{error.message} {JOIN_QUESTION}")
            if answer.lower() == "y":  # anything else means no, and prints nothing
                self._reserve(member, isbn)
            return
        item = self._library.get_item(isbn)
        self._output(format_borrowed(member, item, loan))

    def _reserve(self, member: Member, isbn: str) -> None:
        position = self._library.reserve(member.member_id, isbn)
        item = self._library.get_item(isbn)
        self._output(format_waiting_joined(member, item, position))

    # --- Options 4 to 6: return, renew, join the waiting list -----------------------------

    def _return_item(self) -> None:
        loan_id = self._ask("Loan ID: ")
        result = self._library.return_item(loan_id, self._today)
        self._output(format_returned(result))

    def _renew(self) -> None:
        loan_id = self._ask("Loan ID: ")
        result = self._library.renew(loan_id, self._today)
        self._output(format_renewed(result))

    def _join_waiting_list(self) -> None:
        member = self._ask_member()
        isbn = self._ask("ISBN: ")
        self._reserve(member, isbn)

    # --- Options 7 and 8: reports ---------------------------------------------------------

    def _member_loans(self) -> None:
        member_id = self._ask("Member ID: ")
        report = self._library.member_loans(member_id, self._today)
        self._output(format_member_loans(report))

    def _overdue_report(self) -> None:
        report = self._library.overdue_report(self._today)
        self._output(format_overdue_report(report, self._today))

    # --- Option 9: undo ----------------------------------------------------------------

    def _undo(self) -> None:
        self._output(format_undone(self._library.undo()))

    # --- Option 0 -----------------------------------------------------------------------

    def _exit(self) -> None:
        self._running = False