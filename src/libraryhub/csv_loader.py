"""Reads the four starter CSV files and fills the repositories.

One small function per file returns plain objects. `load_data` calls them and
fills the repositories, so the Library never opens a file itself.
"""

from __future__ import annotations

import csv
import re
from datetime import date
from typing import TYPE_CHECKING, TypeVar

from libraryhub.errors import LibraryError, ValidationError
from libraryhub.items import Book, ItemType, Magazine, ReferenceItem
from libraryhub.loans import Fine, Loan
from libraryhub.members import PremiumMember, RegularMember, StudentMember

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from libraryhub.items import LibraryItem
    from libraryhub.members import Member
    from libraryhub.repositories import (
        FineRepository,
        ItemRepository,
        LoanRepository,
        MemberRepository,
    )

ITEMS_FILE = "books.csv"
MEMBERS_FILE = "members.csv"
LOANS_FILE = "loans.csv"
FINES_FILE = "fines.csv"

# Dictionary lookups choose the class from the CSV text. No if-chain, so adding
# a new kind means adding one line here.
ITEM_CLASSES: dict[str, type[LibraryItem]] = {
    ItemType.BOOK.value: Book,
    ItemType.MAGAZINE.value: Magazine,
    ItemType.REFERENCE.value: ReferenceItem,
}
MEMBER_CLASSES: dict[str, type[Member]] = {
    "Student": StudentMember,
    "Regular": RegularMember,
    "Premium": PremiumMember,
}
YES_NO = {"yes": True, "no": False}

_INT_PATTERN = re.compile(r"-?[0-9]+")
_DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")  # YYYY-MM-DD only

T = TypeVar("T")


# --- Reading one cell --------------------------------------------------------


def _field(row: dict[str, str], name: str) -> str:
    value = row.get(name)
    if value is None:
        raise ValidationError(name, f"missing column '{name}'")
    return value.strip()


def _to_int(text: str, name: str) -> int:
    if not _INT_PATTERN.fullmatch(text):
        raise ValidationError(name, f"{name} must be a whole number, got '{text}'")
    return int(text)


def _to_date(text: str, name: str) -> date:
    try:
        if not _DATE_PATTERN.fullmatch(text):
            raise ValueError(text)
        return date.fromisoformat(text)
    except ValueError:
        raise ValidationError(
            name, f"{name} must be a date like 2026-10-12, got '{text}'"
        ) from None


def _to_optional_date(text: str, name: str) -> date | None:
    return None if text == "" else _to_date(text, name)


def _to_paid(text: str) -> bool:
    try:
        return YES_NO[text.lower()]
    except KeyError:
        raise ValidationError("paid", f"paid must be yes or no, got '{text}'") from None


def _split_authors(text: str) -> list[str]:
    return [name.strip() for name in text.split(";") if name.strip()]


def _choose_class(table: dict[str, type[T]], text: str, name: str) -> type[T]:
    try:
        return table[text]
    except KeyError:
        known = ", ".join(table)
        raise ValidationError(
            name, f"unknown {name} '{text}' (expected one of: {known})"
        ) from None


# --- Reading one file --------------------------------------------------------


def _read_rows(path: Path) -> list[tuple[int, dict[str, str]]]:
    # utf-8-sig reads files with or without the invisible BOM that Excel adds.
    try:
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)  # columns are read by name
            return [(reader.line_num, row) for row in reader]
    except UnicodeDecodeError:
        raise ValidationError(
            "file", f"{path.name} is not valid UTF-8 text. Save it as CSV UTF-8."
        ) from None
    except OSError as error:
        raise ValidationError(
            "file", f"cannot read {path.name}: {error.strerror}"
        ) from error


def _load_file(path: Path, build: Callable[[dict[str, str]], T]) -> list[T]:
    """Build one object per row. A bad row names the file and line."""
    objects: list[T] = []
    for line, row in _read_rows(path):
        try:
            objects.append(build(row))
        except LibraryError as error:
            raise ValidationError(
                "file", f"{path.name} line {line}: {error.message}"
            ) from error
    return objects


# --- One builder and one loader per file -------------------------------------


def _build_item(row: dict[str, str]) -> LibraryItem:
    item_class = _choose_class(ITEM_CLASSES, _field(row, "item_type"), "item_type")
    return item_class(
        isbn=_field(row, "isbn"),
        title=_field(row, "title"),
        authors=_split_authors(_field(row, "authors")),
        category=_field(row, "category"),
        parent_category=_field(row, "parent_category") or None,
        pages=_to_int(_field(row, "pages"), "pages"),
        price=_to_int(_field(row, "price"), "price"),
        total_copies=_to_int(_field(row, "total_copies"), "total_copies"),
    )


def _build_member(row: dict[str, str]) -> Member:
    member_class = _choose_class(
        MEMBER_CLASSES, _field(row, "membership_type"), "membership_type"
    )
    return member_class(
        _field(row, "member_id"), _field(row, "name"), _field(row, "email")
    )


def _build_loan(row: dict[str, str]) -> Loan:
    return Loan(
        _field(row, "member_id"),
        _field(row, "isbn"),
        _to_date(_field(row, "issue_date"), "issue_date"),
        _to_date(_field(row, "due_date"), "due_date"),
        loan_id=_field(row, "loan_id"),
        return_date=_to_optional_date(_field(row, "return_date"), "return_date"),
    )


def _build_fine(row: dict[str, str]) -> Fine:
    return Fine(
        _field(row, "loan_id"),
        _to_int(_field(row, "amount"), "amount"),
        _to_paid(_field(row, "paid")),
    )


def load_items(path: Path) -> list[LibraryItem]:
    return _load_file(path, _build_item)


def load_members(path: Path) -> list[Member]:
    return _load_file(path, _build_member)


def load_loans(path: Path) -> list[Loan]:
    return _load_file(path, _build_loan)


def load_fines(path: Path) -> list[Fine]:
    return _load_file(path, _build_fine)


# --- Checking the data as a whole --------------------------------------------


def _check_unique(field: str, label: str, values: list[str]) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ValidationError(field, f"{label} {value} appears more than once.")
        seen.add(value)


def _check_data(
    items: list[LibraryItem],
    members: list[Member],
    loans: list[Loan],
    fines: list[Fine],
) -> None:
    """Each ID is unique and every loan and fine points at something real.

    A fine for a missing loan would crash unpaid_total later, or worse, quietly
    unblock a member, so bad data is stopped here.
    """
    _check_unique("isbn", "ISBN", [item.isbn for item in items])
    _check_unique("member_id", "Member", [member.member_id for member in members])
    _check_unique("loan_id", "Loan", [loan.loan_id for loan in loans])
    _check_unique("loan_id", "Fine for loan", [fine.loan_id for fine in fines])

    isbns = {item.isbn for item in items}
    member_ids = {member.member_id for member in members}
    loan_ids = {loan.loan_id for loan in loans}
    for loan in loans:
        if loan.member_id not in member_ids:
            raise ValidationError(
                "member_id",
                f"Loan {loan.loan_id} names unknown member {loan.member_id}.",
            )
        if loan.isbn not in isbns:
            raise ValidationError(
                "isbn", f"Loan {loan.loan_id} names unknown ISBN {loan.isbn}."
            )
    for fine in fines:
        if fine.loan_id not in loan_ids:
            raise ValidationError(
                "loan_id", f"A fine names unknown loan {fine.loan_id}."
            )


def load_data(
    data_dir: Path,
    items: ItemRepository,
    members: MemberRepository,
    loans: LoanRepository,
    fines: FineRepository,
) -> None:
    """Fill the four (empty) repositories from the four files in `data_dir`.

    All or nothing: every file is read and checked first, and only then is
    anything stored. A broken file leaves the repositories untouched.
    """
    item_list = load_items(data_dir / ITEMS_FILE)
    member_list = load_members(data_dir / MEMBERS_FILE)
    loan_list = load_loans(data_dir / LOANS_FILE)
    fine_list = load_fines(data_dir / FINES_FILE)
    _check_data(item_list, member_list, loan_list, fine_list)

    for item in item_list:
        items.add(item)
    for member in member_list:
        members.add(member)
    for loan in loan_list:
        loans.add(loan)
    for fine in fine_list:
        fines.add(fine)