import pytest

from libraryhub.dsa.recursion import (
    binary_search_recursive,
    factorial,
    fibonacci,
    sum_of_digits,
)
from libraryhub.errors import ValidationError

# --- factorial ------------------------------------------------------------------


def test_factorial_matches_the_brief():
    assert factorial(5) == 120


@pytest.mark.parametrize(
    ("n", "expected"), [(0, 1), (1, 1), (2, 2), (3, 6), (10, 3_628_800)]
)
def test_factorial_values(n, expected):
    assert factorial(n) == expected


# --- fibonacci ---------------------------------------------------------------------


def test_fibonacci_matches_the_brief():
    assert fibonacci(7) == 13


def test_fibonacci_first_ten_numbers():
    assert [fibonacci(n) for n in range(10)] == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


# --- sum_of_digits -------------------------------------------------------------------


def test_sum_of_digits_matches_the_brief():
    assert sum_of_digits(4096) == 19


@pytest.mark.parametrize(
    ("n", "expected"), [(0, 0), (7, 7), (10, 1), (999, 27), (1000, 1)]
)
def test_sum_of_digits_values(n, expected):
    assert sum_of_digits(n) == expected


@pytest.mark.parametrize("function", [factorial, fibonacci, sum_of_digits])
def test_negative_numbers_are_refused(function):
    with pytest.raises(ValidationError):
        function(-1)


# --- binary_search_recursive ------------------------------------------------------------

ISBNS = [
    "9780000000011",
    "9780000000028",
    "9780000000035",
    "9780000000042",
    "9780000000059",
    "9780000000066",
    "9780000000073",
]


@pytest.mark.parametrize("position", range(len(ISBNS)))
def test_every_value_is_found_at_its_own_index(position):
    assert binary_search_recursive(ISBNS, ISBNS[position]) == position


def test_a_missing_value_gives_minus_one():
    assert binary_search_recursive(ISBNS, "9780000000050") == -1
    assert binary_search_recursive(ISBNS, "0000000000000") == -1  # before all
    assert binary_search_recursive(ISBNS, "9999999999999") == -1  # after all


def test_an_empty_list_gives_minus_one():
    assert binary_search_recursive([], "9780000000011") == -1


def test_a_large_list_needs_only_a_few_levels():
    isbns = [f"{number:013d}" for number in range(100_000)]
    assert binary_search_recursive(isbns, isbns[99_999]) == 99_999
    assert binary_search_recursive(isbns, isbns[0]) == 0
    assert binary_search_recursive(isbns, "9999999999999") == -1