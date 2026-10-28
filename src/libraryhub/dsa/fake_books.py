"""Makes valid fake books so we can measure the library at any size."""

from __future__ import annotations

import random

from libraryhub.items import Book
from libraryhub.library import Library
from libraryhub.repositories import (
    InMemoryFineRepository,
    InMemoryItemRepository,
    InMemoryLoanRepository,
    InMemoryMemberRepository,
)

CATEGORIES = ["Biography", "Fiction", "History", "Programming", "Software Engineering"]
WORDS = ["River", "Stone", "Garden", "Signal", "Harbour", "Orbit", "Lantern", "Compass"]
AUTHORS = ["A. Rao", "B. Khan", "C. Iyer", "D. Mehta", "E. Nair", "F. Das"]


def make_fake_books(n: int, seed: int = 42) -> list[Book]:
    """n books with valid, unique 13-digit ISBNs. Same seed, same books."""
    rng = random.Random(seed)
    books = []
    for i in range(n):
        isbn = f"{9781000000000 + i:013d}"  # never clashes with the starter ISBNs
        title = f"{rng.choice(WORDS)} {rng.choice(WORDS)} {i}"
        authors = rng.sample(AUTHORS, k=rng.randint(1, 2))
        category = rng.choice(CATEGORIES)
        books.append(
            Book(isbn, title, authors, category, None,
                 rng.randint(50, 1200), rng.randint(100, 1500), rng.randint(1, 3))
        )
    return books
from types import SimpleNamespace


def load_fake_world(n: int, seed: int = 42) -> SimpleNamespace:
    """The library plus the repositories behind it, for benchmarks."""
    items = InMemoryItemRepository()
    for book in make_fake_books(n, seed):
        items.add(book)
    members = InMemoryMemberRepository()
    loans = InMemoryLoanRepository()
    fines = InMemoryFineRepository()
    library = Library(items, members, loans, fines)
    return SimpleNamespace(library=library, members=members, loans=loans)


def load_fake_library(n: int, seed: int = 42) -> Library:
    """A Library holding n fake books and no members, loans or fines."""
    return load_fake_world(n, seed).library