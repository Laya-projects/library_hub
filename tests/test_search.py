from types import SimpleNamespace

import pytest

from libraryhub.dsa.search import (
    binary_search,
    binary_search_counted,
    linear_search_by_title,
)

STARTER_ISBNS = [
    "9780000000011",
    "9780000000028",
    "9780000000035",
    "9780000000042",
    "9780000000059",
    "9780000000066",
    "9780000000073",
]


def books(*titles):
    """Tiny stand-ins: linear search only reads .title."""
    return [SimpleNamespace(title=title) for title in titles]


# --- Linear search by title -----------------------------------------------------


def test_linear_search_on_an_empty_list():
    assert linear_search_by_title([], "Sapiens") == -1


def test_linear_search_one_element_found():
    assert linear_search_by_title(books("Sapiens"), "Sapiens") == 0


def test_linear_search_one_element_not_found():
    assert linear_search_by_title(books("Sapiens"), "Clean Code") == -1


def test_linear_search_first_element():
    assert linear_search_by_title(books("A", "B", "C"), "A") == 0


def test_linear_search_last_element():
    assert linear_search_by_title(books("A", "B", "C"), "C") == 2


def test_linear_search_not_found():
    assert linear_search_by_title(books("A", "B", "C"), "Z") == -1


def test_linear_search_ignores_capitalisation():
    assert linear_search_by_title(books("Wings of Fire"), "wINGS OF fIRE") == 0


def test_linear_search_returns_the_first_of_two_matches():
    assert linear_search_by_title(books("A", "B", "B"), "B") == 1


# --- Binary search --------------------------------------------------------------


def test_binary_search_on_an_empty_list():
    assert binary_search([], "9780000000011") == -1
    assert binary_search_counted([], "9780000000011") == (-1, 0)


def test_binary_search_one_element_found():
    assert binary_search_counted(["x"], "x") == (0, 1)


def test_binary_search_one_element_not_found():
    assert binary_search_counted(["x"], "y") == (-1, 1)


def test_binary_search_first_element():
    assert binary_search(STARTER_ISBNS, STARTER_ISBNS[0]) == 0


def test_binary_search_last_element():
    assert binary_search(STARTER_ISBNS, STARTER_ISBNS[-1]) == 6


def test_binary_search_matches_the_brief_sample_for_a_found_isbn():
    assert binary_search_counted(STARTER_ISBNS, "9780000000066") == (5, 2)


def test_binary_search_matches_the_brief_sample_for_a_missing_isbn():
    assert binary_search_counted(STARTER_ISBNS, "9780000000050") == (-1, 3)


def test_binary_search_not_found_before_the_first_and_after_the_last():
    assert binary_search(STARTER_ISBNS, "9780000000000") == -1
    assert binary_search(STARTER_ISBNS, "9780000000099") == -1


@pytest.mark.parametrize("size", [1, 2, 3, 4, 7, 8, 100])
def test_binary_search_finds_every_element_of_any_size(size):
    values = [f"{i:05d}" for i in range(size)]
    for index, value in enumerate(values):
        assert binary_search(values, value) == index


def test_binary_search_agrees_with_list_index_on_many_values():
    values = [f"{i * 3:06d}" for i in range(500)]
    for probe in range(0, 1500, 7):
        text = f"{probe:06d}"
        expected = values.index(text) if text in values else -1
        assert binary_search(values, text) == expected


def test_binary_search_uses_few_comparisons():
    values = [f"{i:06d}" for i in range(1024)]
    _, comparisons = binary_search_counted(values, "000000")
    assert comparisons <= 11  # about log2(1024) + 1, nowhere near 1024