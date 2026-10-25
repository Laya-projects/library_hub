"""Sets and dicts at work: duplicates, grouping, counting and two-sum.

A dict or set finds a key in O(1) on average, because the key's hash tells
Python where to look. That one fact is behind every function in this file.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

# --- 2.3a Duplicates when importing a books CSV -----------------------------------


@dataclass(frozen=True)
class ImportReport:
    rows: int
    added: int
    duplicates: list[str]  # one message per skipped duplicate, in file order

    def summary(self) -> str:
        skipped = len(self.duplicates)
        noun = "duplicate" if skipped == 1 else "duplicates"
        return f"Imported {self.rows} rows: {self.added} added, {skipped} {noun} skipped."


def scan_books_csv(path: Path, isbn_column: str = "isbn", title_column: str = "title") -> ImportReport:
    """Read a books CSV and report every repeated ISBN with its line number.

    `seen` maps ISBN -> title of the first row that used it. Asking "have I seen
    this ISBN?" is one dict lookup, so the whole file is read in one pass.
    """
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    rows = 0
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows += 1
            isbn = row[isbn_column].strip()
            line = reader.line_num  # the real line in the file (the header is line 1)
            if isbn in seen:
                duplicates.append(
                    f"Line {line}: duplicate ISBN {isbn} "
                    f"(already used by '{seen[isbn]}'), skipped."
                )
            else:
                seen[isbn] = row[title_column].strip()
    return ImportReport(rows, rows - len(duplicates), duplicates)


# --- 2.3b Grouping: author -> titles --------------------------------------------------


class _HasAuthors(Protocol):
    @property
    def title(self) -> str: ...

    @property
    def authors(self) -> Sequence[str]: ...


def group_by_author(items: Iterable[_HasAuthors]) -> dict[str, list[str]]:
    """Each author mapped to their titles. Authors come out A to Z."""
    groups: defaultdict[str, list[str]] = defaultdict(list)
    for item in items:
        for author in item.authors:
            groups[author].append(item.title)
    return {author: groups[author] for author in sorted(groups)}


def format_authors(groups: Mapping[str, Sequence[str]]) -> str:
    return "\n".join(f"{author}: {', '.join(titles)}" for author, titles in groups.items())


# --- 2.3c Frequency counting: most borrowed titles ------------------------------------


def most_borrowed(
    borrowed_isbns: Iterable[str], titles: Mapping[str, str], top: int = 3
) -> list[tuple[str, int]]:
    """(title, times borrowed), most first; equal counts are ordered A to Z.

    `borrowed_isbns` has one ISBN per loan, returned or not. `titles` maps ISBN
    to title (a dict built once, so each lookup is O(1)).
    """
    counts = Counter(borrowed_isbns)
    ranked = sorted(
        ((titles[isbn], count) for isbn, count in counts.items()),
        key=lambda pair: (-pair[1], pair[0]),
    )
    return ranked[:top]


def format_most_borrowed(ranked: Sequence[tuple[str, int]]) -> str:
    width = max((len(title) for title, _ in ranked), default=0)
    return "\n".join(
        f"{place}. {title.ljust(width)}  {count}"
        for place, (title, count) in enumerate(ranked, start=1)
    )


# --- 2.3d Reading challenge: two-sum in one pass ----------------------------------------


class _Readable(Protocol):
    @property
    def title(self) -> str: ...

    @property
    def pages(self) -> int: ...

    def is_borrowable(self) -> bool: ...


def reading_challenge(
    items: Iterable[_Readable], target_pages: int
) -> tuple[_Readable, _Readable] | None:
    """Two different borrowable items whose pages add up to `target_pages`.

    One pass: for each item, the page count we would need to have seen already is
    `target_pages - item.pages`. If that is in `seen`, we are done. Otherwise
    remember this item and move on. Reference items are skipped.
    """
    seen: dict[int, _Readable] = {}
    for item in items:
        if not item.is_borrowable():
            continue
        partner = seen.get(target_pages - item.pages)
        if partner is not None:  # checked before adding, so never the same item twice
            return partner, item
        seen.setdefault(item.pages, item)
    return None


def format_reading_challenge(
    pair: tuple[_Readable, _Readable] | None, target_pages: int
) -> str:
    if pair is None:
        return "No pair found."
    first, second = pair
    return (
        f"{first.title} ({first.pages}) + {second.title} ({second.pages}) "
        f"= {target_pages}"
    )