"""Report the repeated ISBNs in a books CSV.

Usage:  python import_books.py books_with_duplicate.csv
"""

import sys
from pathlib import Path

from libraryhub.dsa.hashing import scan_books_csv


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python import_books.py <books.csv>")
        return 2
    report = scan_books_csv(Path(argv[1]))
    for message in report.duplicates:
        print(message)
    print(report.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))