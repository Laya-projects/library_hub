"""The console menu. It reads choices and prints; it holds no rule logic.

Every rule lives in `Library`. The menu asks the Library, then prints what
comes back or the formatted error. Input and output are injected so a test can
script the whole conversation.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from libraryhub.errors import LibraryError
from libraryhub.formatters import format_catalogue, format_search_results

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import date

    from libraryhub.items import LibraryItem
    from libraryhub.library import Library

MENU_TEXT = """=== LibraryHub Mini ===
1. List catalogue
2. Search by title or author
3. Borrow
4. Return
5. Renew
6. Join waiting list
7. Member loans
8. Overdue report
0. Exit"""

PROMPT = "> "
INVALID_CHOICE = "Please enter a number from 0 to 8."


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
            "3": partial(self._not_built, "3"),
            "4": partial(self._not_built, "4"),
            "5": partial(self._not_built, "5"),
            "6": partial(self._not_built, "6"),
            "7": partial(self._not_built, "7"),
            "8": partial(self._not_built, "8"),
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

    # --- Actions ----------------------------------------------------------------

    def _exit(self) -> None:
        self._running = False

    def _not_built(self, choice: str) -> None:
        self._output(f"Option {choice} is not built yet.")

    def _with_availability(
        self, items: list[LibraryItem]
    ) -> list[tuple[LibraryItem, int]]:
        """Pair each item with the copies available now, for the formatters."""
        return [(item, self._library.available_copies(item.isbn)) for item in items]

    def _list_catalogue(self) -> None:
        entries = self._with_availability(self._library.list_items())
        self._output(format_catalogue(entries))

    def _search(self) -> None:
        text = self._ask("Search: ")
        entries = self._with_availability(self._library.search_items(text))
        self._output(format_search_results(text, entries))