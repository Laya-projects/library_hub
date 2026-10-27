"""Recursion warm-ups (Phase 2, step 8).

Every recursive function needs two things, written down before the code:
  1. a base case: an input so small that the answer is known without recursing;
  2. a smaller problem: each call must move closer to that base case.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from libraryhub.errors import ValidationError

if TYPE_CHECKING:
    from collections.abc import Sequence


def _require_not_negative(n: int) -> None:
    if n < 0:
        raise ValidationError("n", "n cannot be negative.")


def factorial(n: int) -> int:
    """n! = n * (n-1) * ... * 1.

    Base case: n == 0 gives 1.
    Smaller problem: n becomes n - 1. Calls: n + 1, so O(n) time and O(n) stack.
    """
    _require_not_negative(n)
    if n == 0:
        return 1
    return n * factorial(n - 1)


def fibonacci(n: int) -> int:
    """The n-th Fibonacci number, with fibonacci(0) = 0 and fibonacci(1) = 1.

    Base case: n < 2 gives n itself.
    Smaller problem: n becomes n - 1 and n - 2.
    Each call makes two more calls, so the time is about O(2^n): the same
    values are worked out again and again. It is fine for a warm-up and far too
    slow for n = 50.
    """
    _require_not_negative(n)
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def sum_of_digits(n: int) -> int:
    """sum_of_digits(4096) is 4 + 0 + 9 + 6 = 19.

    Base case: n < 10 (one digit) gives n itself.
    Smaller problem: drop the last digit with n // 10 and add it back with n % 10.
    Calls: one per digit, so O(d) for a number with d digits.
    """
    _require_not_negative(n)
    if n < 10:
        return n
    return n % 10 + sum_of_digits(n // 10)


def binary_search_recursive(
    values: Sequence[str], target: str, low: int = 0, high: int | None = None
) -> int:
    """Index of `target` in the sorted `values`, or -1 when it is not there.

    Base case: low > high means nothing is left to search, so the answer is -1.
    Smaller problem: the range values[low..high] is cut in half each call.
    Calls: about log2(n), so 100,000 items need at most 17 levels: safe.
    No slicing: slicing would copy half the list on every call.
    """
    if high is None:
        high = len(values) - 1
    if low > high:
        return -1
    middle = (low + high) // 2
    if values[middle] == target:
        return middle
    if values[middle] < target:
        return binary_search_recursive(values, target, middle + 1, high)
    return binary_search_recursive(values, target, low, middle - 1)