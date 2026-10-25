from types import SimpleNamespace

from libraryhub.dsa.hashing import (
    format_authors,
    format_most_borrowed,
    format_reading_challenge,
    group_by_author,
    most_borrowed,
    reading_challenge,
    scan_books_csv,
)


def book(title, authors, pages, borrowable=True):
    return SimpleNamespace(
        title=title, authors=authors, pages=pages, is_borrowable=lambda: borrowable
    )


# --- duplicates ---------------------------------------------------------------------

HEADER = "isbn,title\n"


def write_csv(tmp_path, *lines):
    path = tmp_path / "books.csv"
    path.write_text(HEADER + "".join(line + "\n" for line in lines), encoding="utf-8")
    return path


def test_duplicate_isbn_is_reported_with_its_line_number(tmp_path):
    path = write_csv(
        tmp_path,
        "9780000000011,Wings of Fire",
        "9780000000042,Python Crash Course",
        "9780000000042,Python Crash Course",
    )
    report = scan_books_csv(path)
    expected = (
        "Line 4: duplicate ISBN 9780000000042 "
        "(already used by 'Python Crash Course'), skipped."
    )
    assert report.duplicates == [expected]
    assert report.summary() == "Imported 3 rows: 2 added, 1 duplicate skipped."


def test_a_file_without_duplicates_reports_none(tmp_path):
    path = write_csv(tmp_path, "9780000000011,A", "9780000000028,B")
    report = scan_books_csv(path)
    assert report.duplicates == []
    assert report.summary() == "Imported 2 rows: 2 added, 0 duplicates skipped."


def test_several_duplicates_each_get_their_own_line(tmp_path):
    path = write_csv(tmp_path, "1,A", "1,A", "2,B", "2,B", "1,A")
    report = scan_books_csv(path)
    assert [m.split(":")[0] for m in report.duplicates] == ["Line 3", "Line 5", "Line 6"]


# --- grouping -----------------------------------------------------------------------


def test_group_by_author_splits_authors_and_sorts_them():
    items = [
        book("Wings of Fire", ["A.P.J. Abdul Kalam", "Arun Tiwari"], 180),
        book("Python Crash Course", ["Eric Matthes"], 544),
        book("Encyclopaedia of Science", ["Various"], 1200),
        book("India Today (Oct 2026)", ["Various"], 90),
    ]
    groups = group_by_author(items)
    assert list(groups) == ["A.P.J. Abdul Kalam", "Arun Tiwari", "Eric Matthes", "Various"]
    assert groups["Various"] == ["Encyclopaedia of Science", "India Today (Oct 2026)"]
    assert format_authors(groups).splitlines()[-1] == (
        "Various: Encyclopaedia of Science, India Today (Oct 2026)"
    )


def test_group_by_author_on_nothing():
    assert group_by_author([]) == {}


# --- frequency ----------------------------------------------------------------------

TITLES = {"A": "Wings of Fire", "B": "Python Crash Course", "C": "Clean Code", "D": "Sapiens"}


def test_most_borrowed_orders_by_count_then_title():
    ranked = most_borrowed(["A", "B", "A", "B", "A", "B", "C"], TITLES, top=3)
    assert ranked == [("Python Crash Course", 3), ("Wings of Fire", 3), ("Clean Code", 1)]


def test_most_borrowed_respects_top_and_empty_input():
    assert most_borrowed(["A", "A", "B"], TITLES, top=1) == [("Wings of Fire", 2)]
    assert most_borrowed([], TITLES) == []


def test_format_most_borrowed_numbers_the_lines():
    text = format_most_borrowed([("Python Crash Course", 3), ("Wings of Fire", 3)])
    assert text == "1. Python Crash Course  3\n2. Wings of Fire        3"


# --- reading challenge ------------------------------------------------------------------

STARTER = [
    book("Wings of Fire", ["x"], 180),
    book("The Alchemist", ["x"], 208),
    book("Clean Code", ["x"], 464),
    book("Python Crash Course", ["x"], 544),
    book("Sapiens", ["x"], 512),
    book("Encyclopaedia of Science", ["x"], 1200, borrowable=False),
    book("India Today (Oct 2026)", ["x"], 90),
]


def test_reading_challenge_724():
    pair = reading_challenge(STARTER, 724)
    assert format_reading_challenge(pair, 724) == (
        "Wings of Fire (180) + Python Crash Course (544) = 724"
    )


def test_reading_challenge_720():
    pair = reading_challenge(STARTER, 720)
    assert format_reading_challenge(pair, 720) == (
        "The Alchemist (208) + Sapiens (512) = 720"
    )


def test_reading_challenge_no_pair():
    assert reading_challenge(STARTER, 1000) is None
    assert format_reading_challenge(None, 1000) == "No pair found."


def test_reference_items_are_excluded():
    # 1200 + 90 = 1290 would work only with the reference encyclopaedia
    assert reading_challenge(STARTER, 1290) is None


def test_an_item_is_never_paired_with_itself():
    assert reading_challenge([book("A", ["x"], 100)], 200) is None


def test_two_different_items_with_equal_pages_can_pair():
    pair = reading_challenge([book("A", ["x"], 100), book("B", ["x"], 100)], 200)
    assert pair is not None and (pair[0].title, pair[1].title) == ("A", "B")