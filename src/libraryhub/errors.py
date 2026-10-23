"""Exceptions for LibraryHub.

Every failure is a LibraryError that carries a ``code`` and a ``message``.
The console menu and the Phase 4 API both read from these objects, so the
wording of every error lives here and nowhere else.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date


class LibraryError(Exception):
    """Parent of every error the library raises."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def formatted(self) -> str:
        """The one place that builds the ``ERROR [code]: message`` line."""
        return f"ERROR [{self.code}]: {self.message}"


# --- Errors that print their class name as the code -----------------------


class InvalidISBNError(LibraryError):
    """The ISBN is not exactly 13 digits (R9). The code is the class name."""

    def __init__(self, isbn: str) -> None:
        super().__init__("InvalidISBNError", "ISBN must be exactly 13 digits.")
        self.isbn = isbn


class ItemNotFoundError(LibraryError):
    """The ISBN is well formed but no catalogue item has it."""

    def __init__(self, isbn: str) -> None:
        super().__init__("ItemNotFoundError", f"No item with ISBN {isbn}.")
        self.isbn = isbn


class MemberNotFoundError(LibraryError):
    """No member has this ID."""

    def __init__(self, member_id: str) -> None:
        super().__init__("MemberNotFoundError", f"No member with ID {member_id}.")
        self.member_id = member_id


class LoanNotFoundError(LibraryError):
    def __init__(self, loan_id: str) -> None:
        super().__init__("LoanNotFoundError", f"No loan with ID {loan_id}.")
        self.loan_id = loan_id


class LoanAlreadyReturnedError(LibraryError):
    """The loan is closed, so it cannot be returned or renewed again."""

    def __init__(self, loan_id: str, returned_on: date) -> None:
        super().__init__(
            "LoanAlreadyReturnedError",
            f"Loan {loan_id} was already returned on {returned_on.isoformat()}.",
        )
        self.loan_id = loan_id
        self.returned_on = returned_on


class ValidationError(LibraryError):
    """A value is not acceptable (blank title, negative copies, bad email...).

    The classes check their own data and raise this, so the menu and the API
    only ever have to catch one family of errors: LibraryError.
    """

    def __init__(self, field: str, message: str) -> None:
        super().__init__("ValidationError", message)
        self.field = field


# --- Rule violations: the code is the rule number -------------------------


class ItemNotBorrowableError(LibraryError):
    """R1: reference items can never be borrowed."""

    def __init__(self, title: str) -> None:
        super().__init__(
            "R1", f"'{title}' is a reference item and cannot be borrowed."
        )
        self.title = title


class UnpaidFinesError(LibraryError):
    """R4: unpaid fines are above the limit."""

    def __init__(self, member_name: str, unpaid: int, limit: int) -> None:
        super().__init__(
            "R4",
            f"{member_name} has unpaid fines of ₹{unpaid} (limit ₹{limit}).",
        )
        self.member_name = member_name
        self.unpaid = unpaid
        self.limit = limit


class BorrowLimitExceededError(LibraryError):
    """R3: the member already holds as many items as their membership allows."""

    def __init__(self, member_name: str, on_loan: int, limit: int) -> None:
        super().__init__(
            "R3",
            f"{member_name} already has {on_loan} of {limit} items on loan.",
        )
        self.member_name = member_name
        self.on_loan = on_loan
        self.limit = limit


class DuplicateLoanError(LibraryError):
    """R8: a member cannot hold two copies of the same title."""

    def __init__(self, member_name: str, title: str) -> None:
        super().__init__(
            "R8", f"{member_name} already has a copy of '{title}'."
        )
        self.member_name = member_name
        self.title = title


class ItemNotAvailableError(LibraryError):
    """R7: no copy is free, so the member may join the waiting list.

    The message is only the first half of the prompt. The menu adds
    "Join the waiting list? (y/n)" itself.
    """

    def __init__(self, title: str) -> None:
        super().__init__("R7", f"No copies of '{title}' are available.")
        self.title = title


class RenewalNotAllowedError(LibraryError):
    """R2 or R6: the code depends on the situation, so use a factory method.

    The inherited ``__init__(code, message)`` is used by the three factories.
    """

    @classmethod
    def magazine(cls) -> RenewalNotAllowedError:
        return cls("R2", "Magazines cannot be renewed.")

    @classmethod
    def limit_reached(cls, title: str, times: int) -> RenewalNotAllowedError:
        unit = "time" if times == 1 else "times"
        return cls("R6", f"'{title}' has already been renewed {times} {unit}.")

    @classmethod
    def someone_waiting(cls, title: str) -> RenewalNotAllowedError:
        return cls(
            "R6", f"'{title}' cannot be renewed because another member is waiting."
        )