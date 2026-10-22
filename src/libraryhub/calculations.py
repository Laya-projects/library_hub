"""Pure calculation functions for dates and money.

A pure function takes inputs and returns a result. It never reads the clock,
a file or any global state, so "today" always arrives as a parameter and every
worked example in the brief is a one-line test.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import date

    from libraryhub.items import LibraryItem
    from libraryhub.loans import Fine, Loan
    from libraryhub.members import Member

UNPAID_FINE_LIMIT = 100  # R4: unpaid fines above this many rupees block borrowing


def due_date(issue_date: date, item: LibraryItem, member: Member) -> date:
    """Issue date plus the loan period for this item and member (R2)."""
    return issue_date + timedelta(days=item.loan_period_for(member))


def days_late(due_date: date, today: date, return_date: date | None = None) -> int:
    """Days late (R10).

    The due date itself is not late and the day after is 1. A returned loan
    stops counting on its return date, so it never gets later.
    """
    last_day = today if return_date is None else return_date
    return max(0, (last_day - due_date).days)


def fine_amount(days_late: int, rate_per_day: int, item_price: int) -> int:
    """Days late times the daily rate, never more than the item's price (R5)."""
    return min(days_late * rate_per_day, item_price)


def renewed_due_date(current_due_date: date, member: Member) -> date:
    """A renewal adds the member's loan period to the current due date (R6)."""
    return current_due_date + timedelta(days=member.loan_period_days())


def unpaid_total(
    member_id: str, fines: Iterable[Fine], loans: Iterable[Loan]
) -> int:
    """Sum of the unpaid fines of one member (D1).

    A fine knows its loan and not its member, so the member is found through
    the loan. Building a dict from loan ID to loan first makes each lookup one
    step. A fine whose loan is missing raises KeyError: that is corrupt data
    and must not quietly unblock a member.
    """
    loans_by_id = {loan.loan_id: loan for loan in loans}
    return sum(
        fine.amount
        for fine in fines
        if not fine.paid and loans_by_id[fine.loan_id].member_id == member_id
    )


def exceeds_fine_limit(unpaid: int, limit: int = UNPAID_FINE_LIMIT) -> bool:
    """True only when the amount is above the limit (R4). Exactly the limit is fine."""
    return unpaid > limit