"""Repositories: the only code that stores and finds data.

`Library` talks to the four interfaces below and never to a file or a dict.
In Phase 3 the in-memory versions are swapped for database ones and `Library`
does not change.

`get` returns None when nothing is found. The repository only stores things;
the Library decides which error to raise (D7).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from libraryhub.errors import LoanNotFoundError, ValidationError

if TYPE_CHECKING:
    from libraryhub.items import LibraryItem
    from libraryhub.loans import Fine, Loan
    from libraryhub.members import Member


# --- Interfaces --------------------------------------------------------------


class ItemRepository(ABC):
    @abstractmethod
    def get(self, isbn: str) -> LibraryItem | None:
        """The item with this ISBN, or None."""

    @abstractmethod
    def add(self, item: LibraryItem) -> None:
        """Store an item. An ISBN identifies one title, so a repeat is refused (R9)."""

    @abstractmethod
    def list_all(self) -> list[LibraryItem]:
        """Every item."""

    @abstractmethod
    def count(self) -> int:
        """How many items are stored."""


class MemberRepository(ABC):
    @abstractmethod
    def get(self, member_id: str) -> Member | None:
        """The member with this ID, or None."""

    @abstractmethod
    def add(self, member: Member) -> None:
        """Store a member. A repeated ID is refused."""

    @abstractmethod
    def list_all(self) -> list[Member]:
        """Every member."""

    @abstractmethod
    def count(self) -> int:
        """How many members are stored."""


class LoanRepository(ABC):
    @abstractmethod
    def add(self, loan: Loan) -> None:
        """Store a loan. A repeated loan ID is refused."""

    @abstractmethod
    def get(self, loan_id: str) -> Loan | None:
        """The loan with this ID, or None."""

    @abstractmethod
    def update(self, loan: Loan) -> None:
        """Save changes to a stored loan (return date, renewals, due date).

        A database repository only sees a change when this is called.
        """

    @abstractmethod
    def list_all(self) -> list[Loan]:
        """Every loan, open and returned."""

    @abstractmethod
    def list_open(self) -> list[Loan]:
        """Loans that have not been returned."""

    @abstractmethod
    def list_for_member(self, member_id: str) -> list[Loan]:
        """Every loan of one member."""

    @abstractmethod
    def list_for_isbn(self, isbn: str) -> list[Loan]:
        """Every loan of one title."""

    @abstractmethod
    def remove(self, loan_id: str) -> None:
        """Delete a loan. Used only to undo a borrow."""


class FineRepository(ABC):
    @abstractmethod
    def add(self, fine: Fine) -> None:
        """Store a fine. A loan has at most one fine, so a repeat is refused."""

    @abstractmethod
    def list_all(self) -> list[Fine]:
        """Every fine, paid and unpaid."""

    @abstractmethod
    def remove_for_loan(self, loan_id: str) -> None:
        """Delete the fine recorded for this loan, if any. Used to undo a return."""


# --- In-memory versions ------------------------------------------------------
# list_all() hands out a copy of the collection, so callers cannot add to or
# remove from what is stored. The objects inside are shared on purpose: Library
# must be able to mark a Fine as paid or set a loan's return_date.


class InMemoryItemRepository(ItemRepository):
    def __init__(self) -> None:
        self._items: dict[str, LibraryItem] = {}  # dict by ISBN: unique key (R9)

    def get(self, isbn: str) -> LibraryItem | None:
        return self._items.get(isbn)

    def add(self, item: LibraryItem) -> None:
        if item.isbn in self._items:
            raise ValidationError(
                "isbn", f"An item with ISBN {item.isbn} already exists."
            )
        self._items[item.isbn] = item

    def list_all(self) -> list[LibraryItem]:
        return list(self._items.values())

    def count(self) -> int:
        return len(self._items)


class InMemoryMemberRepository(MemberRepository):
    def __init__(self) -> None:
        self._members: dict[str, Member] = {}  # dict by member ID

    def get(self, member_id: str) -> Member | None:
        return self._members.get(member_id)

    def add(self, member: Member) -> None:
        if member.member_id in self._members:
            raise ValidationError(
                "member_id", f"A member with ID {member.member_id} already exists."
            )
        self._members[member.member_id] = member

    def list_all(self) -> list[Member]:
        return list(self._members.values())

    def count(self) -> int:
        return len(self._members)


class InMemoryLoanRepository(LoanRepository):
    def __init__(self) -> None:
        self._loans: list[Loan] = []  # list: loans keep the order they were made

    def add(self, loan: Loan) -> None:
        if self.get(loan.loan_id) is not None:
            raise ValidationError(
                "loan_id", f"A loan with ID {loan.loan_id} already exists."
            )
        self._loans.append(loan)

    def get(self, loan_id: str) -> Loan | None:
        for loan in self._loans:
            if loan.loan_id == loan_id:
                return loan
        return None

    def update(self, loan: Loan) -> None:
        for index, stored in enumerate(self._loans):
            if stored.loan_id == loan.loan_id:
                self._loans[index] = loan  # same place in the list
                return
        raise LoanNotFoundError(loan.loan_id)

    def list_all(self) -> list[Loan]:
        return list(self._loans)

    def list_open(self) -> list[Loan]:
        return [loan for loan in self._loans if loan.is_open()]

    def list_for_member(self, member_id: str) -> list[Loan]:
        return [loan for loan in self._loans if loan.member_id == member_id]

    def list_for_isbn(self, isbn: str) -> list[Loan]:
        return [loan for loan in self._loans if loan.isbn == isbn]

    def remove(self, loan_id: str) -> None:
        for index, loan in enumerate(self._loans):
            if loan.loan_id == loan_id:
                del self._loans[index]
                return
        raise LoanNotFoundError(loan_id)

class InMemoryFineRepository(FineRepository):
    def __init__(self) -> None:
        self._fines: list[Fine] = []

    def add(self, fine: Fine) -> None:
        if any(stored.loan_id == fine.loan_id for stored in self._fines):
            raise ValidationError(
                "loan_id", f"A fine for loan {fine.loan_id} already exists."
            )
        self._fines.append(fine)

    def list_all(self) -> list[Fine]:
        return list(self._fines)
    
    def remove_for_loan(self, loan_id: str) -> None:
        self._fines = [fine for fine in self._fines if fine.loan_id != loan_id]