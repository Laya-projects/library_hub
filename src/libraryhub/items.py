"""Library items: books, magazines and reference items."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

from libraryhub.errors import InvalidISBNError, ItemNotBorrowableError

if TYPE_CHECKING:
    from libraryhub.members import Member

MAGAZINE_LOAN_DAYS = 7  # R2: magazines are loaned for 7 days, whatever the member
BOOK_MAX_RENEWALS = 2  # R6: a book can be renewed up to 2 times

# R9: exactly 13 digits. [0-9] is used on purpose: str.isdigit() would also
# accept digits from other scripts.
_ISBN_PATTERN = re.compile(r"[0-9]{13}")


class ItemType(Enum):
    """The three kinds of item. The values match the CSV file."""

    BOOK = "Book"
    MAGAZINE = "Magazine"
    REFERENCE = "Reference"


class LibraryItem(ABC):
    """Something the library holds. Subclasses decide how it can be lent."""

    def __init__(
        self,
        isbn: str,
        title: str,
        authors: list[str],
        category: str,
        parent_category: str | None,
        pages: int,
        price: int,
        total_copies: int,
    ) -> None:
        self.isbn = isbn  # these three go through their setters, so they are checked
        self.title = title
        self.total_copies = total_copies
        self.authors = list(authors)  # own copy, so outside changes cannot leak in
        self.category = category
        self.parent_category = parent_category
        self.pages = pages
        self.price = price  # whole rupees

    @property
    def isbn(self) -> str:
        return self._isbn

    @isbn.setter
    def isbn(self, value: str) -> None:
        if not _ISBN_PATTERN.fullmatch(value):
            raise InvalidISBNError(value)
        self._isbn = value

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        if not value.strip():
            raise ValueError("Title cannot be blank.")
        self._title = value.strip()

    @property
    def total_copies(self) -> int:
        return self._total_copies

    @total_copies.setter
    def total_copies(self, value: int) -> None:
        if value < 0:
            raise ValueError("Copies cannot be negative.")
        self._total_copies = value

    @abstractmethod
    def item_type(self) -> ItemType:
        """Which kind of item this is."""

    @abstractmethod
    def is_borrowable(self) -> bool:
        """Can this item leave the library at all? (R1)"""

    @abstractmethod
    def loan_period_for(self, member: Member) -> int:
        """How many days this item is loaned to this member."""

    @abstractmethod
    def max_renewals(self) -> int:
        """How many times a loan of this item may be renewed."""

    def __str__(self) -> str:
        return f"{self.title} ({self.item_type().value}, ISBN {self.isbn})"

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(isbn={self.isbn!r}, title={self.title!r}, "
            f"authors={self.authors!r}, category={self.category!r}, "
            f"parent_category={self.parent_category!r}, pages={self.pages}, "
            f"price={self.price}, total_copies={self.total_copies})"
        )


class Book(LibraryItem):
    def item_type(self) -> ItemType:
        return ItemType.BOOK

    def is_borrowable(self) -> bool:
        return True

    def loan_period_for(self, member: Member) -> int:
        return member.loan_period_days()

    def max_renewals(self) -> int:
        return BOOK_MAX_RENEWALS


class Magazine(LibraryItem):
    def item_type(self) -> ItemType:
        return ItemType.MAGAZINE

    def is_borrowable(self) -> bool:
        return True

    def loan_period_for(self, member: Member) -> int:
        return MAGAZINE_LOAN_DAYS  # the member is ignored on purpose (R2)

    def max_renewals(self) -> int:
        return 0  # R2: magazines cannot be renewed


class ReferenceItem(LibraryItem):
    def item_type(self) -> ItemType:
        return ItemType.REFERENCE

    def is_borrowable(self) -> bool:
        return False  # R1

    def loan_period_for(self, member: Member) -> int:
        # Library.borrow() checks is_borrowable() first, so this is never
        # reached in normal use. Failing loudly beats returning a made-up number.
        raise ItemNotBorrowableError(self.title)

    def max_renewals(self) -> int:
        return 0