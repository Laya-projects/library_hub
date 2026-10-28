"""Complexity audit: time five Library methods at four sizes.

Run:  python benchmarks/audit.py
"""

from datetime import date

from libraryhub.dsa.fake_books import load_fake_world
from libraryhub.dsa.timing import median_ms, median_ms_with_setup
from libraryhub.loans import Loan
from libraryhub.members import StudentMember

TODAY = date(2026, 10, 12)  # never read the clock
SIZES = [1_000, 5_000, 10_000, 50_000]


def world_with_member(n):
    world = load_fake_world(n)
    world.members.add(StudentMember("M001", "Asha Raman", "asha@example.com"))
    return world


def middle_isbn(n):
    return f"{9781000000000 + n // 2:013d}"


def measure_list_items(n):
    world = world_with_member(n)
    return median_ms(world.library.list_items)


def measure_search(n):
    world = world_with_member(n)
    return median_ms(lambda: world.library.search_items("River"))


def measure_borrow(n):
    isbn = middle_isbn(n)
    return median_ms_with_setup(
        lambda: world_with_member(n),
        lambda world: world.library.borrow("M001", isbn, TODAY),
    )


def measure_return(n):
    isbn = middle_isbn(n)

    def setup():
        world = world_with_member(n)
        loan = world.library.borrow("M001", isbn, TODAY)  # not timed
        return world, loan

    return median_ms_with_setup(
        setup, lambda state: state[0].library.return_item(state[1].loan_id, TODAY)
    )


def measure_overdue(n):
    world = world_with_member(n)
    for i in range(n // 10):  # 10% of the books are on an overdue loan
        isbn = f"{9781000000000 + i:013d}"
        world.loans.add(Loan("M001", isbn, date(2026, 9, 1), date(2026, 9, 22)))
    return median_ms(lambda: world.library.overdue_report(TODAY))


MEASURES = {
    "list_items": measure_list_items,
    "search_items": measure_search,
    "borrow": measure_borrow,
    "return_item": measure_return,
    "overdue_report": measure_overdue,
}


def main():
    print("| method | " + " | ".join(f"n={n:,}" for n in SIZES) + " |")
    print("|---|" + "---|" * len(SIZES))
    for name, measure in MEASURES.items():
        cells = [f"{measure(n):.3f}" for n in SIZES]
        print(f"| {name} | " + " | ".join(cells) + " |")  # milliseconds


if __name__ == "__main__":
    main()