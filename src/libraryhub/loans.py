"""Loans and fines. They hold IDs only and are told what they need to know."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from datetime import date

    from libraryhub.items import LibraryItem
    from libraryhub.members import Member


@dataclass
class Fine:
    """A fine for one late loan. The unpaid total is calculated, never stored."""

    loan_id: str
    amount: int  # whole rupees
    paid: bool = False

    def __str__(self) -> str:
        status = "paid" if self.paid else "unpaid"
        return f"Fine for {self.loan_id}: ₹{self.amount} ({status})"


class Loan:
    """One item lent to one member. It refers to both by ID (D3)."""

    # Class attribute: one counter shared by every loan, so each new loan
    # gets a number nobody has used.
    _next_number: ClassVar[int] = 1

    def __init__(
        self,
        member_id: str,
        isbn: str,
        issue_date: date,
        due_date: date,
        *,
        loan_id: str | None = None,
        return_date: date | None = None,
        renewals: int = 0,
    ) -> None:
        if loan_id is None:
            loan_id = Loan._take_next_id()
        else:
            Loan._note_existing(loan_id)  # loaded loans must not be reused
        # Instance attributes: every loan has its own ID, people and dates.
        self.loan_id = loan_id
        self.member_id = member_id
        self.isbn = isbn
        self.issue_date = issue_date
        self.due_date = due_date
        self.return_date = return_date
        self.renewals = renewals

    @classmethod
    def _take_next_id(cls) -> str:
        loan_id = f"L{cls._next_number:03d}"
        cls._next_number += 1
        return loan_id

    @classmethod
    def _note_existing(cls, loan_id: str) -> None:
        match = re.fullmatch(r"L(\d+)", loan_id)
        if match:
            cls._next_number = max(cls._next_number, int(match.group(1)) + 1)

    @classmethod
    def reset_numbering(cls) -> None:
        """Start numbering from L001 again. Tests use this for a clean start."""
        cls._next_number = 1

    def is_open(self) -> bool:
        """True while the item has not been returned."""
        return self.return_date is None

    def days_late(self, today: date) -> int:
        """Days late (R10). Due date itself is not late; the day after is 1.

        Once the item is returned, lateness stops counting on the return date.
        """
        last_day = today if self.return_date is None else self.return_date
        return max(0, (last_day - self.due_date).days)

    def is_overdue(self, today: date) -> bool:
        return self.is_open() and self.days_late(today) > 0

    def fine(self, today: date, member: Member, item: LibraryItem) -> int:
        """R5: days late x the member's daily rate, never above the item's price."""
        return min(self.days_late(today) * member.fine_per_day(), item.price)

    def __str__(self) -> str:
        state = "on loan" if self.is_open() else "returned"
        return (
            f"{self.loan_id}: {self.member_id} has {self.isbn}, "
            f"due {self.due_date.isoformat()} ({state})"
        )

    def __repr__(self) -> str:
        returned = None if self.return_date is None else self.return_date.isoformat()
        return (
            f"Loan(loan_id={self.loan_id!r}, member_id={self.member_id!r}, "
            f"isbn={self.isbn!r}, issue_date={self.issue_date.isoformat()}, "
            f"due_date={self.due_date.isoformat()}, return_date={returned}, "
            f"renewals={self.renewals})"
        )