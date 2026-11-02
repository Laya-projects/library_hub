import pytest

from libraryhub.errors import InvalidISBNError, ValidationError
from libraryhub.items import Book


def make_book(isbn="9780000000099", copies=1):
    return Book(
        isbn=isbn, title="Fluent Python", authors=["Luciano Ramalho"],
        category="Programming", parent_category="Technology",
        pages=800, price=900, total_copies=copies,
    )


def test_add_item_makes_it_findable(library_world):
    library = library_world.library
    library.add_item(make_book())
    assert library.get_item("9780000000099").title == "Fluent Python"
    assert library.available_copies("9780000000099") == 1


def test_add_item_refuses_a_repeated_isbn(library_world):
    library = library_world.library
    library.add_item(make_book())
    with pytest.raises(ValidationError):
        library.add_item(make_book())


def test_add_item_needs_at_least_one_copy(library_world):
    with pytest.raises(ValidationError):
        library_world.library.add_item(make_book(copies=0))


def test_add_item_rejects_a_bad_isbn_before_anything_is_stored(library_world):
    with pytest.raises(InvalidISBNError):
        make_book(isbn="123")