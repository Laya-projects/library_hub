"""Pure functions that turn library data into the exact text of the brief.

No printing, no input and no calls to Library: the menu hands in data and
prints what comes back.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Container, Sequence
    from datetime import date

    from libraryhub.items import LibraryItem
    from libraryhub.library import (
        MemberLoans,
        OverdueLine,
        RenewResult,
        ReturnResult,
    )
    from libraryhub.loans import Loan
    from libraryhub.members import Member

COLUMN_GAP = "  "  # two spaces between columns, as in every sample


def format_money(amount: int) -> str:
    """Whole rupees, no decimals: 300 becomes '₹300'."""
    return f"₹{amount}"


def format_days(days: int) -> str:
    """'1 day' or '20 days', so the program never says '1 days'."""
    return f"{days} day" if days == 1 else f"{days} days"


def format_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    right_aligned: Container[str] = (),
) -> str:
    """Aligned plain-text table.

    Each column is as wide as its longest cell (header included) and columns
    are separated by two spaces. Columns named in `right_aligned` are pushed to
    the right. The last column is not padded, so no line ends in spaces.
    """
    widths = [max(len(cell) for cell in column) for column in zip(headers, *rows)]
    last = len(headers) - 1

    lines: list[str] = []
    for row in [headers, *rows]:
        cells: list[str] = []
        for index, (cell, width) in enumerate(zip(row, widths)):
            if headers[index] in right_aligned:
                cells.append(cell.rjust(width))
            elif index == last:
                cells.append(cell)
            else:
                cells.append(cell.ljust(width))
        lines.append(COLUMN_GAP.join(cells))
    return "\n".join(lines)


def _availability_text(item: LibraryItem, available: int) -> str:
    if not item.is_borrowable():
        return "not borrowable"
    return f"{available} of {item.total_copies}"


def format_catalogue(entries: Sequence[tuple[LibraryItem, int]]) -> str:
    """Catalogue table. Each entry is (item, copies available now)."""
    rows = [
        [
            item.isbn,
            item.title,
            item.item_type().value,
            _availability_text(item, available),
        ]
        for item, available in entries
    ]
    return format_table(["ISBN", "TITLE", "TYPE", "AVAILABLE"], rows)


def format_search_results(
    query: str, entries: Sequence[tuple[LibraryItem, int]]
) -> str:
    """'1 result:' or 'N results:' and one line per item, or 'No items match'."""
    if not entries:
        return f"No items match '{query}'."

    count = "1 result:" if len(entries) == 1 else f"{len(entries)} results:"
    lines = [count]
    for item, available in entries:
        authors = ", ".join(item.authors)
        availability = _availability_text(item, available)
        lines.append(f"{item.isbn}  {item.title}  ({authors})  {availability}")
    return "\n".join(lines)


def _loan_status(days_late: int) -> str:
    if days_late <= 0:
        return "On loan"
    return f"OVERDUE ({format_days(days_late)})"


def format_member_loans(member_loans: MemberLoans) -> str:
    """Header, table of active loans, then the active count and unpaid fines."""
    member = member_loans.member
    header = (
        f"Loans for {member.name} "
        f"({member.membership_label()}: {member.borrow_limit()} items, "
        f"{member.loan_period_days()} days, {format_money(member.fine_per_day())}/day)"
    )
    footer = (
        f"Active loans: {len(member_loans.lines)} of {member.borrow_limit()}\n"
        f"Unpaid fines: {format_money(member_loans.unpaid_fines)}"
    )
    if not member_loans.lines:
        return f"{header}\nNo active loans.\n{footer}"

    rows = [
        [
            line.loan.loan_id,
            line.item.title,
            line.loan.issue_date.isoformat(),
            line.loan.due_date.isoformat(),
            _loan_status(line.days_late),
        ]
        for line in member_loans.lines
    ]
    table = format_table(["LOAN", "TITLE", "ISSUED", "DUE", "STATUS"], rows)
    return f"{header}\n{table}\n{footer}"


def format_overdue_report(lines: Sequence[OverdueLine], today: date) -> str:
    """Overdue table with DAYS right-aligned, then the totals line."""
    header = f"Overdue loans as of {today.isoformat()}"
    total_fines = sum(line.fine_so_far for line in lines)
    footer = f"Total overdue: {len(lines)}   Fines so far: {format_money(total_fines)}"
    if not lines:
        return f"{header}\nNo overdue loans.\n{footer}"

    rows = [
        [
            line.loan.loan_id,
            line.member.name,
            line.item.title,
            line.loan.due_date.isoformat(),
            str(line.days_late),
            format_money(line.fine_so_far),
        ]
        for line in lines
    ]
    table = format_table(
        ["LOAN", "MEMBER", "TITLE", "DUE", "DAYS", "FINE SO FAR"],
        rows,
        right_aligned=["DAYS"],
    )
    return f"{header}\n{table}\n{footer}"


# --- The one-sentence answers to borrow, return, renew and reserve ------------


def format_borrowed(member: Member, item: LibraryItem, loan: Loan) -> str:
    """OK: Asha Raman borrowed 'Wings of Fire'. Due 2026-10-26."""
    return (
        f"OK: {member.name} borrowed '{item.title}'. "
        f"Due {loan.due_date.isoformat()}."
    )


def format_returned(result: ReturnResult) -> str:
    """The return message, plus who is next in line when someone is waiting."""
    if result.days_late == 0:
        lateness = "Returned on time."
    else:
        lateness = f"Late by {format_days(result.days_late)}."
    text = (
        f"OK: {result.member.name} returned '{result.item.title}'. "
        f"{lateness} Fine: {format_money(result.fine)}."
    )
    if result.next_waiting is not None:
        text += f"\nNext on waiting list: {result.next_waiting.name}."
    if result.still_waiting:
        text += "\n" + format_waiting_list(result.item, result.still_waiting)
    return text


def format_renewed(result: RenewResult) -> str:
    """OK: Renewed 'Sapiens' (renewal 1 of 2). New due date 2026-11-19."""
    return (
        f"OK: Renewed '{result.item.title}' "
        f"(renewal {result.renewal_number} of {result.max_renewals}). "
        f"New due date {result.new_due_date.isoformat()}."
    )


def format_waiting_joined(member: Member, item: LibraryItem, position: int) -> str:
    """OK: Sneha Iyer is #1 on the waiting list for 'The Alchemist'."""
    return f"OK: {member.name} is #{position} on the waiting list for '{item.title}'."

def format_waiting_list(item: LibraryItem, members: Sequence[Member]) -> str:
    """Waiting list for 'The Alchemist': Sneha Iyer, Asha Raman"""
    names = ", ".join(member.name for member in members)
    return f"Waiting list for '{item.title}': {names}"