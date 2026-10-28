"""Compare the hand-written sorts with sorted(), and linear with binary search.

Run:  python benchmarks/sorts.py
The hand-written sorts at n = 10,000 take a while (bubble sort is the slowest).
"""

from libraryhub.dsa.fake_books import make_fake_books
from libraryhub.dsa.search import binary_search, linear_search_by_title
from libraryhub.dsa.sorting import bubble_sort, insertion_sort, selection_sort
from libraryhub.dsa.timing import median_ms

SIZES = [1_000, 5_000, 10_000]
HAND_RUNS = 3  # the slow sorts: few runs
FAST_RUNS = 7


def by_title(book):
    return book.title


def measure_sorts(n):
    """Milliseconds for each sort on n fake books, sorted by title."""
    books = make_fake_books(n)
    return {
        "bubble_sort_ms": median_ms(lambda: bubble_sort(books, key=by_title), HAND_RUNS),
        "insertion_sort_ms": median_ms(
            lambda: insertion_sort(books, key=by_title), HAND_RUNS
        ),
        "selection_sort_ms": median_ms(
            lambda: selection_sort(books, key=by_title), HAND_RUNS
        ),
        "sorted_key_ms": median_ms(lambda: sorted(books, key=by_title), FAST_RUNS),
    }


def measure_searches(n):
    """Milliseconds to find the LAST book (the worst case for linear search)."""
    books = make_fake_books(n)
    isbns = [book.isbn for book in books]  # already in ascending order
    last_title, last_isbn = books[-1].title, isbns[-1]
    return {
        "linear_search_ms": median_ms(
            lambda: linear_search_by_title(books, last_title), 21
        ),
        "binary_search_ms": median_ms(lambda: binary_search(isbns, last_isbn), 21),
    }


def print_table(columns, rows, digits):
    print("| n | " + " | ".join(columns) + " |")
    print("|---|" + "---|" * len(columns))
    for n, values in rows.items():
        cells = [f"{values[c]:,.{digits}f}" for c in columns]
        print(f"| {n:,} | " + " | ".join(cells) + " |")


def main(sizes=SIZES):
    rows = {}
    for n in sizes:
        print(f"measuring n = {n:,} ...", flush=True)
        rows[n] = {**measure_searches(n), **measure_sorts(n)}

    print("\n### Brief-style table (milliseconds)")
    print_table(
        ["linear_search_ms", "binary_search_ms", "sorted_key_ms", "insertion_sort_ms"],
        rows,
        digits=4,
    )

    print("\n### All three hand-written sorts against sorted() (milliseconds)")
    print_table(
        ["bubble_sort_ms", "insertion_sort_ms", "selection_sort_ms", "sorted_key_ms"],
        rows,
        digits=2,
    )

    if len(sizes) >= 2:
        small, big = sizes[-2], sizes[-1]
        print(f"\n### Growth when n goes from {small:,} to {big:,} ({big / small:g}x)")
        print("| column | time ratio |")
        print("|---|---|")
        for column in rows[big]:
            ratio = rows[big][column] / rows[small][column]
            print(f"| {column} | {ratio:.1f}x |")


if __name__ == "__main__":
    main()