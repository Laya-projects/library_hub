"""The Library service: the only place where the rules R1 to R10 are applied.

It works through the repositories and the pure functions in `calculations`.
It never opens a file, never reads the clock (every date-dependent method
takes `today`) and never prints: it returns data or raises a LibraryError, and
the menu or the API decides how to show it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple

from libraryhub import calculations
from libraryhub.audit import AuditLog, audit
from libraryhub.errors import (
    BorrowLimitExceededError,
    DuplicateLoanError,
    ItemNotAvailableError,
    ItemNotBorrowableError,
    ItemNotFoundError,
    LibraryError,
    LoanAlreadyReturnedError,
    LoanNotFoundError,
    MemberNotFoundError,
    RenewalNotAllowedError,
    UnpaidFinesError,
    ValidationError,
)
from libraryhub.items import validate_isbn
from libraryhub.loans import Fine, Loan

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from datetime import date, datetime

    from libraryhub.items import LibraryItem
    from libraryhub.members import Member
    from libraryhub.repositories import (
        FineRepository,
        ItemRepository,
        LoanRepository,
        MemberRepository,
    )

logger = logging.getLogger(__name__)


# --- Small result objects: data for the menu or the API to show -------------


@dataclass(frozen=True)
class ReturnResult:
    loan: Loan
    member: Member
    item: LibraryItem
    days_late: int
    fine: int
    next_waiting: Member | None  # first member in the waiting list, if any


@dataclass(frozen=True)
class RenewResult:
    loan: Loan
    item: LibraryItem
    renewal_number: int
    max_renewals: int
    new_due_date: date


@dataclass(frozen=True)
class LoanLine:
    loan: Loan
    item: LibraryItem
    days_late: int  # 0 when the loan is not overdue


@dataclass(frozen=True)
class MemberLoans:
    member: Member
    lines: list[LoanLine]  # active loans only
    unpaid_fines: int


@dataclass(frozen=True)
class OverdueLine:
    loan: Loan
    member: Member
    item: LibraryItem
    days_late: int
    fine_so_far: int  # calculated, not stored until the item is returned


class UnpaidFineLine(NamedTuple):
    member: Member
    amount: int

    @property
    def fine(self) -> int:
        return self.amount

    @property
    def unpaid(self) -> int:
        return self.amount


class Library:
    def __init__(
        self,
        items: ItemRepository,
        members: MemberRepository,
        loans: LoanRepository,
        fines: FineRepository,
        audit_log: AuditLog | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._items = items
        self._members = members
        self._loans = loans
        self._fines = fines
        self.audit_log = audit_log if audit_log is not None else AuditLog(clock=clock)
        # One first-come, first-served queue of member IDs per ISBN. It lives in
        # memory only and is lost on exit. Phase 3 moves it behind a repository
        # (the reservations table).
        self._waiting: dict[str, list[str]] = {}

    # --- Looking things up (they raise, so callers never meet None) ----------

    def get_member(self, member_id: str) -> Member:
        member = self._members.get(member_id)
        if member is None:
            raise MemberNotFoundError(member_id)
        return member

    def get_item(self, isbn: str) -> LibraryItem:
        validate_isbn(isbn)  # "123" is InvalidISBNError, not "not found"
        item = self._items.get(isbn)
        if item is None:
            raise ItemNotFoundError(isbn)
        return item

    def get_loan(self, loan_id: str) -> Loan:
        loan = self._loans.get(loan_id)
        if loan is None:
            raise LoanNotFoundError(loan_id)
        return loan

    def _get_open_loan(self, loan_id: str) -> Loan:
        loan = self.get_loan(loan_id)
        if loan.return_date is not None:
            raise LoanAlreadyReturnedError(loan.loan_id, loan.return_date)
        return loan

    def list_items(self) -> list[LibraryItem]:
        return self._items.list_all()

    # --- Questions the rules are built on -------------------------------------

    def available_copies(self, isbn: str) -> int:
        """Total copies minus the open loans of this title (D2)."""
        item = self.get_item(isbn)
        out = sum(1 for loan in self._loans.list_for_isbn(isbn) if loan.is_open())
        return item.total_copies - out

    def unpaid_fines_for(self, member_id: str) -> int:
        return calculations.unpaid_total(
            member_id, self._fines.list_all(), self._loans.list_all()
        )

    def _open_loans_of(self, member_id: str) -> list[Loan]:
        return [
            loan for loan in self._loans.list_for_member(member_id) if loan.is_open()
        ]

    def _holds_title(self, member: Member, item: LibraryItem) -> bool:
        open_loans = self._open_loans_of(member.member_id)
        return any(loan.isbn == item.isbn for loan in open_loans)

    def _place_in_line(self, member: Member, item: LibraryItem) -> int:
        """Where this member stands for a free copy: 1 means first in line.

        A queued member keeps their place. Anyone else stands behind the queue.
        """
        queue = self._waiting.get(item.isbn, [])
        if member.member_id in queue:
            return queue.index(member.member_id) + 1
        return len(queue) + 1

    # --- Borrowing: the checks run in the brief's order -----------------------

    def _borrow_checks(self) -> list[Callable[[Member, LibraryItem], None]]:
        """The order of the rules is this list. Reordering is a one-line change."""
        return [
            self._check_borrowable,  # R1
            self._check_fines,  # R4
            self._check_limit,  # R3
            self._check_no_duplicate,  # R8
            self._check_available,  # R7
        ]

    def _check_borrowable(self, member: Member, item: LibraryItem) -> None:
        if not item.is_borrowable():
            raise ItemNotBorrowableError(item.title)

    def _check_fines(self, member: Member, item: LibraryItem) -> None:
        unpaid = self.unpaid_fines_for(member.member_id)
        if calculations.exceeds_fine_limit(unpaid):
            raise UnpaidFinesError(member.name, unpaid, calculations.UNPAID_FINE_LIMIT)

    def _check_limit(self, member: Member, item: LibraryItem) -> None:
        on_loan = len(self._open_loans_of(member.member_id))
        if on_loan >= member.borrow_limit():
            raise BorrowLimitExceededError(member.name, on_loan, member.borrow_limit())

    def _check_no_duplicate(self, member: Member, item: LibraryItem) -> None:
        if self._holds_title(member, item):
            raise DuplicateLoanError(member.name, item.title)

    def _check_available(self, member: Member, item: LibraryItem) -> None:
        if self.available_copies(item.isbn) < self._place_in_line(member, item):
            raise ItemNotAvailableError(item.title)

    @audit("borrow")
    def borrow(self, member_id: str, isbn: str, today: date) -> Loan:
        try:
            member = self.get_member(member_id)
            item = self.get_item(isbn)
            for check in self._borrow_checks():
                check(member, item)  # the first broken rule raises, the rest never run
            loan = Loan(
                member.member_id,
                item.isbn,
                today,
                calculations.due_date(today, item, member),
            )
            self._loans.add(loan)
            queue = self._waiting.get(item.isbn, [])
            if member.member_id in queue:
                queue.remove(member.member_id)  # their turn has come
            logger.info("Borrow successful: member %s borrowed %s", member_id, isbn)
            return loan
        except LibraryError as err:
            logger.warning(
                "Borrow refused: member %s, isbn %s - %s", member_id, isbn, err
            )
            raise

    # --- Returning ------------------------------------------------------------

    @audit("return")
    def return_item(self, loan_id: str, today: date) -> ReturnResult:
        try:
            loan = self._get_open_loan(loan_id)
            member = self.get_member(loan.member_id)
            item = self.get_item(loan.isbn)
            days = loan.days_late(today)
            fine = loan.fine(today, member, item)
            if fine > 0:
                self._fines.add(Fine(loan.loan_id, fine))
            loan.return_date = today  # last, so a failed fine leaves the loan open
            self._loans.update(loan)  # a database repository only sees this call
            queue = self._waiting.get(item.isbn, [])
            next_waiting = self._members.get(queue[0]) if queue else None
            result = ReturnResult(loan, member, item, days, fine, next_waiting)
            logger.info("Return successful: loan %s returned", loan_id)
            return result
        except LibraryError as err:
            logger.warning("Return refused: loan %s - %s", loan_id, err)
            raise

    # --- Renewing ---------------------------------------------------------------

    @audit("renew")
    def renew(self, loan_id: str, today: date) -> RenewResult:
        """Renew a loan (R2, R6).

        `today` is not used: the new due date is the old due date plus the
        member's loan period, so no rule here depends on the date. It is kept so
        borrow, return_item and renew are called the same way.
        """
        try:
            loan = self._get_open_loan(loan_id)
            member = self.get_member(loan.member_id)
            item = self.get_item(loan.isbn)
            if item.max_renewals() == 0:
                raise RenewalNotAllowedError.magazine()  # R2
            if loan.renewals >= item.max_renewals():
                raise RenewalNotAllowedError.limit_reached(
                    item.title, loan.renewals
                )  # R6
            if self._waiting.get(item.isbn):
                raise RenewalNotAllowedError.someone_waiting(item.title)  # R6
            loan.renew(member)
            self._loans.update(loan)
            result = RenewResult(
                loan, item, loan.renewals, item.max_renewals(), loan.due_date
            )
            logger.info(
                "Renewal successful: loan %s renewed to %s", loan_id, loan.due_date
            )
            return result
        except LibraryError as err:
            logger.warning("Renewal refused: loan %s - %s", loan_id, err)
            raise

    # --- The waiting list -------------------------------------------------------

    def reserve(self, member_id: str, isbn: str) -> int:
        """Join the waiting list for a title. Returns the position (1 = first)."""
        member = self.get_member(member_id)
        item = self.get_item(isbn)
        if not item.is_borrowable():
            raise ItemNotBorrowableError(item.title)
        if self._holds_title(member, item):
            raise DuplicateLoanError(member.name, item.title)
        queue = self._waiting.setdefault(item.isbn, [])
        if member.member_id in queue:
            raise ValidationError(
                "waiting_list",
                f"{member.name} is already on the waiting list for '{item.title}'.",
            )
        if self.available_copies(item.isbn) >= self._place_in_line(member, item):
            raise ValidationError(
                "waiting_list",
                f"A copy of '{item.title}' is available. Borrow it instead.",
            )
        queue.append(member.member_id)
        return len(queue)

    # --- Reports ----------------------------------------------------------------

    def member_loans(self, member_id: str, today: date) -> MemberLoans:
        member = self.get_member(member_id)
        lines = [
            LoanLine(loan, self.get_item(loan.isbn), loan.days_late(today))
            for loan in self._open_loans_of(member.member_id)
        ]
        return MemberLoans(member, lines, self.unpaid_fines_for(member.member_id))

    def iter_overdue(self, today: date) -> Iterator[OverdueLine]:
        """Yield overdue loans one at a time."""
        for loan in self._loans.list_open():
            days = loan.days_late(today)
            if days > 0:
                member = self.get_member(loan.member_id)
                item = self.get_item(loan.isbn)
                fine = loan.fine(today, member, item)
                yield OverdueLine(loan, member, item, days, fine)

    def overdue_report(self, today: date) -> list[OverdueLine]:
        """Overdue loans, most days late first."""
        return sorted(
            self.iter_overdue(today),
            key=lambda line: (-line.days_late, line.loan.loan_id),
        )

    def items_by_category(self) -> dict[str, list[str]]:
        """Category mapped to the sorted titles in it."""
        items = self._items.list_all()
        categories = sorted({item.category for item in items if item.category})
        return {
            category: sorted(
                [item.title for item in items if item.category == category],
                key=lambda title: title,
            )
            for category in categories
        }

    def category_report(self) -> dict[str, list[str]]:
        """Alias for items_by_category."""
        return self.items_by_category()

    def members_with_unpaid_fines(self) -> list[UnpaidFineLine]:
        """Members with unpaid fines > 0, largest amount first, ties by name."""
        all_lines = [
            UnpaidFineLine(m, self.unpaid_fines_for(m.member_id))
            for m in self._members.list_all()
        ]
        # filter keeps only members with debt, separating the calculation from the condition.
        owing = filter(lambda line: line.amount > 0, all_lines)
        return sorted(owing, key=lambda line: (-line.amount, line.member.name))

    def unpaid_fines_report(self) -> list[UnpaidFineLine]:
        """Alias for members_with_unpaid_fines."""
        return self.members_with_unpaid_fines()