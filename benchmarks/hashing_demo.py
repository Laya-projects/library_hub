"""Print the hashing samples from the brief, using the real starter data."""

from libraryhub.dsa.hashing import (
    format_authors,
    format_most_borrowed,
    format_reading_challenge,
    group_by_author,
    most_borrowed,
    reading_challenge,
)
from libraryhub.main import build_library

library = build_library()
items = library.list_items()

print("group_by_author():")
print(format_authors(group_by_author(items)))

titles = {item.isbn: item.title for item in items}
isbns = [loan.isbn for loan in library._loans.list_all()]  # one ISBN per loan
print("most_borrowed(3):")
print(format_most_borrowed(most_borrowed(isbns, titles, 3)))

for target in (724, 720, 1000):
    pair = reading_challenge(items, target)
    print(f"reading_challenge({target}) -> {format_reading_challenge(pair, target)}")