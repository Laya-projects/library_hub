"""Phase 2 benchmarks (brief 2.1, 2.2 and 2.4): measured, not guessed.

Every number is the MEDIAN of several runs, because one run is noise. Times are
in milliseconds. The tables print as Markdown, ready to paste into
docs/benchmarks.md.

Run it from the project folder:

    python benchmarks.py                 everything (hand sorts at 10,000 take minutes)
    python benchmarks.py --quick         hand-written sorts only up to 5,000
    python benchmarks.py --only audit    just one part: audit, sorts or queue

The audit world for n books holds n // 10 loans (two thirds open, a third
returned with a fine), so the loan and fine lists grow with n. That is what
makes borrow and return_item grow: they scan those lists.
"""

from __future__ import annotations

import argparse
import statistics
import time
from collections import deque
from datetime import date, timedelta
from functools import partial
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from libraryhub import calculations
from libraryhub.dsa.fake_books import load_fake_world, make_fake_books
from libraryhub.dsa.search import binary_search, linear_search_by_title
from libraryhub.dsa.sorting import (
    bubble_sort,
    catalogue_sort,
    insertion_sort,
    selection_sort,
)
from libraryhub.loans import Fine, Loan
from libraryhub.members import RegularMember

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

TODAY = date(2026, 10, 12)  # the project's fixed "today"
AUDIT_SIZES = (1_000, 5_000, 10_000, 50_000)  # brief 2.1
SORT_SIZES = (1_000, 5_000, 10_000)  # brief 2.2
QUEUE_SIZES = (10_000, 50_000, 100_000)  # brief 2.4 asks for 100,000
RUNS = 7  # fast things: the median of 7 runs
SLOW_RUNS = 3  # the hand-written sorts: minutes at 10,000, so only 3 runs
QUEUE_RUNS = 5
QUICK_LIMIT = 5_000  # with --quick, hand sorts stop here
LOANS_PER_BOOKS = 10  # n books come with n // 10 loans
SKIPPED = "skipped"


# --- Helpers ------------------------------------------------------------------


def median_ms(function: Callable[[], Any], runs: int = RUNS, inner: int = 1) -> float:
    """Median time of one call, in ms. `inner` repeats a very fast call and divides."""
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        for _ in range(inner):
            function()
        times.append((time.perf_counter() - start) * 1000 / inner)
    return statistics.median(times)


def median_ms_then_undo(
    library: Any, action: Callable[[], Any], runs: int = RUNS
) -> float:
    """Time `action` (a borrow or a return), then undo it OUTSIDE the timing.

    The undo puts the library back exactly as it was, so every run measures the
    same situation.
    """
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        action()
        times.append((time.perf_counter() - start) * 1000)
        library.undo()
    return statistics.median(times)


def fmt(ms: float | None) -> str:
    if ms is None:
        return SKIPPED
    return f"{ms:,.3f}" if ms < 1 else f"{ms:,.1f}"


def print_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    print("| " + " | ".join(headers) + " |")
    print("|" + "---|" * len(headers))
    for row in rows:
        print("| " + " | ".join(row) + " |")
    print()


def by_title(book: Any) -> str:
    return str(book.title)


# --- 2.1 The complexity audit: five Library methods ---------------------------------


def build_audit_world(n: int) -> SimpleNamespace:
    """n books, n // 10 loans, and the fines of the returned ones.

    Loan number k belongs to member k // 5 (a RegularMember may hold 5) and to
    book k, so no title runs out of copies. By k % 3:
      0: open and overdue (issued 60 days ago)
      1: open and not late (issued 5 days ago)
      2: returned 9 days late, with a fine of 45
    One extra member holds nothing and is the one who borrows in the benchmark.
    """
    world = load_fake_world(n)
    library = world.library
    books = make_fake_books(n)
    loan_count = n // LOANS_PER_BOOKS
    member_count = loan_count // 5 + 2
    for number in range(member_count):
        world.members.add(
            RegularMember(f"M{number:05d}", f"Member {number}", f"m{number}@example.com")
        )
    overdue_ids: list[str] = []
    fines = 0
    for k in range(loan_count):
        member = library.get_member(f"M{k // 5:05d}")
        item = library.get_item(books[k].isbn)
        issued = TODAY - (timedelta(days=5) if k % 3 == 1 else timedelta(days=60))
        loan = Loan(
            member.member_id,
            item.isbn,
            issued,
            calculations.due_date(issued, item, member),
        )
        if k % 3 == 2:
            loan.return_date = TODAY - timedelta(days=30)
        world.loans.add(loan)
        if k % 3 == 2:
            library._fines.add(Fine(loan.loan_id, 45))  # the setup may reach inside
            fines += 1
        if k % 3 == 0:
            overdue_ids.append(loan.loan_id)
    return SimpleNamespace(
        library=library,
        last_title=books[-1].title,
        free_isbn=books[-1].isbn,  # no loan was made for this book
        free_member=f"M{member_count - 1:05d}",
        last_overdue_loan=overdue_ids[-1],  # near the END of the loan list
        loans=loan_count,
        fines=fines,
    )


def audit_table() -> None:
    print("## The five Library methods (median ms)\n")
    rows = []
    for n in AUDIT_SIZES:
        world = build_audit_world(n)
        library = world.library
        list_ms = median_ms(library.list_items)
        search_ms = median_ms(partial(library.search_items, world.last_title))
        borrow_ms = median_ms_then_undo(
            library, partial(library.borrow, world.free_member, world.free_isbn, TODAY)
        )
        return_ms = median_ms_then_undo(
            library, partial(library.return_item, world.last_overdue_loan, TODAY)
        )
        overdue_ms = median_ms(partial(library.overdue_report, TODAY))
        rows.append(
            [
                f"{n:,}",
                f"{world.loans:,}",
                f"{world.fines:,}",
                fmt(list_ms),
                fmt(search_ms),
                fmt(borrow_ms),
                fmt(return_ms),
                fmt(overdue_ms),
            ]
        )
    print_table(
        [
            "n books",
            "loans",
            "fines",
            "list_items_ms",
            "search_items_ms",
            "borrow_ms",
            "return_item_ms",
            "overdue_report_ms",
        ],
        rows,
    )


# --- 2.2 Searching and sorting ----------------------------------------------------------


def measure_search_and_sorts(n: int, quick: bool) -> dict[str, float | None]:
    books = make_fake_books(n)
    isbns = sorted(book.isbn for book in books)
    hand_sorts_allowed = not quick or n <= QUICK_LIMIT

    def timed_sort(sort: Callable[..., Any]) -> float | None:
        if not hand_sorts_allowed:
            return None
        return median_ms(partial(sort, books, key=by_title), runs=SLOW_RUNS)

    return {
        "linear": median_ms(partial(linear_search_by_title, books, books[-1].title)),
        "binary": median_ms(partial(binary_search, isbns, isbns[-1]), inner=1_000),
        "sorted_key": median_ms(partial(sorted, books, key=by_title)),
        "bubble": timed_sort(bubble_sort),
        "insertion": timed_sort(insertion_sort),
        "selection": timed_sort(selection_sort),
        "catalogue": median_ms(partial(catalogue_sort, books)),
    }


def search_and_sort_tables(quick: bool) -> None:
    results = {n: measure_search_and_sorts(n, quick) for n in SORT_SIZES}

    print("## Search and sort, the brief's table (median ms)\n")
    print_table(
        ["n", "linear_search_ms", "binary_search_ms", "sorted_key_ms", "insertion_sort_ms"],
        [
            [
                f"{n:,}",
                fmt(r["linear"]),
                fmt(r["binary"]),
                fmt(r["sorted_key"]),
                fmt(r["insertion"]),
            ]
            for n, r in results.items()
        ],
    )

    print("## Your three sorts against sorted(key=...) (median ms)\n")
    print_table(
        ["n", "bubble", "insertion", "selection", "sorted(key=)", "catalogue_sort"],
        [
            [
                f"{n:,}",
                fmt(r["bubble"]),
                fmt(r["insertion"]),
                fmt(r["selection"]),
                fmt(r["sorted_key"]),
                fmt(r["catalogue"]),
            ]
            for n, r in results.items()
        ],
    )


# --- 2.4 list.pop(0) against deque.popleft() ------------------------------------------------


def drain_list(n: int) -> None:
    queue = [f"M{number}" for number in range(n)]
    while queue:
        queue.pop(0)  # every other entry moves one step to the left: O(n)


def drain_deque(n: int) -> None:
    queue = deque(f"M{number}" for number in range(n))
    while queue:
        queue.popleft()  # only the front pointer moves: O(1)


def queue_table() -> None:
    print("## Serving everybody from the front: pop(0) against popleft() (median ms)\n")
    rows = []
    for n in QUEUE_SIZES:
        list_ms = median_ms(partial(drain_list, n), runs=QUEUE_RUNS)
        deque_ms = median_ms(partial(drain_deque, n), runs=QUEUE_RUNS)
        rows.append(
            [f"{n:,}", fmt(list_ms), fmt(deque_ms), f"{list_ms / deque_ms:,.0f}x"]
        )
    print_table(["n", "list.pop(0)_ms", "deque.popleft()_ms", "list is slower by"], rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--quick", action="store_true", help="hand sorts only up to 5,000 books"
    )
    parser.add_argument(
        "--only", choices=["audit", "sorts", "queue"], help="run just one part"
    )
    args = parser.parse_args()
    if args.only in (None, "audit"):
        audit_table()
    if args.only in (None, "sorts"):
        search_and_sort_tables(args.quick)
    if args.only in (None, "queue"):
        queue_table()


if __name__ == "__main__":
    main()