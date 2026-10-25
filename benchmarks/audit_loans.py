"""Borrow and return as the number of loans grows (n fixed)."""

from datetime import date

from audit import TODAY, middle_isbn, world_with_member  # same folder
from libraryhub.dsa.timing import median_ms_with_setup
from libraryhub.loans import Loan

N = 1_000
LOAN_COUNTS = [1_000, 2_000, 5_000, 10_000]


def world_with_loans(count):
    world = world_with_member(N)
    isbn = f"{9781000000000:013d}"  # book 0; the target book is in the middle
    for _ in range(count):  # on a different member, so the R3 limit is not hit
        world.loans.add(Loan("M900", isbn, date(2026, 10, 1), date(2026, 10, 15)))
    return world


def main():
    isbn = middle_isbn(N)
    print("| method | " + " | ".join(f"L={c:,}" for c in LOAN_COUNTS) + " |")
    print("|---|" + "---|" * len(LOAN_COUNTS))
    borrow = [
        median_ms_with_setup(
            lambda c=c: world_with_loans(c),
            lambda w: w.library.borrow("M001", isbn, TODAY),
            runs=5,
        )
        for c in LOAN_COUNTS
    ]
    print("| borrow | " + " | ".join(f"{t:.3f}" for t in borrow) + " |")

    def setup(c):
        world = world_with_loans(c)
        return world, world.library.borrow("M001", isbn, TODAY)  # not timed

    returns = [
        median_ms_with_setup(
            lambda c=c: setup(c),
            lambda s: s[0].library.return_item(s[1].loan_id, TODAY),
            runs=5,
        )
        for c in LOAN_COUNTS
    ]
    print("| return_item | " + " | ".join(f"{t:.3f}" for t in returns) + " |")


if __name__ == "__main__":
    main()