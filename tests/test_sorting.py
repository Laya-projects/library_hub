"""Three sorts written by hand, so we can see (and time) what sorted() hides.

Each function sorts a COPY and returns it. The list you pass in is not changed.
Set trace=True to print the list after every pass, as in the brief.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, TypeVar

T = TypeVar("T")


def _identity(value: T) -> Any:
    return value


def bubble_sort(
    items: Sequence[T],
    key: Callable[[T], Any] | None = None,
    trace: bool = False,
) -> list[T]:
    """Swap neighbours that are out of order. After pass k the k largest are placed.

    Stable: equal items are never swapped, so they keep their order.
    Time O(n^2); O(n) if the list is already sorted (the early exit below).
    """
    key = key or _identity
    data = list(items)  # the copy: the caller's list stays untouched
    if trace:
        print(f"bubble_sort({list(items)})")
    for pass_number in range(1, len(data)):  # n - 1 passes at most
        swapped = False
        for i in range(len(data) - pass_number):  # the end is already sorted
            if key(data[i]) > key(data[i + 1]):  # strict > keeps it stable
                data[i], data[i + 1] = data[i + 1], data[i]
                swapped = True
        if trace:
            print(f"  after pass {pass_number}: {data}")
        if not swapped:
            break  # a pass with no swaps means it is sorted
    return data


def insertion_sort(
    items: Sequence[T],
    key: Callable[[T], Any] | None = None,
    trace: bool = False,
) -> list[T]:
    """Take each item in turn and slide it left into the sorted part.

    Stable: it only moves past items that are strictly greater.
    Time O(n^2), but close to O(n) on a nearly sorted list.
    """
    key = key or _identity
    data = list(items)
    if trace:
        print(f"insertion_sort({list(items)})")
    for index in range(1, len(data)):
        current = data[index]
        j = index - 1
        while j >= 0 and key(data[j]) > key(current):
            data[j + 1] = data[j]  # shift the bigger item one place right
            j -= 1
        data[j + 1] = current
        if trace:
            print(f"  after inserting index {index}: {data}")
    return data


def selection_sort(
    items: Sequence[T],
    key: Callable[[T], Any] | None = None,
    trace: bool = False,
) -> list[T]:
    """Find the smallest of the rest and swap it into place.

    NOT stable: the swap carries an item across others. Example: sorting
    [(2, 'a'), (2, 'b'), (1, 'c')] by the number swaps (2, 'a') to the far end,
    so it lands after (2, 'b').
    Time O(n^2) always, but at most n - 1 swaps.
    """
    key = key or _identity
    data = list(items)
    if trace:
        print(f"selection_sort({list(items)})")
    for pass_number in range(1, len(data)):  # n - 1 passes
        start = pass_number - 1
        smallest = start
        for i in range(start + 1, len(data)):
            if key(data[i]) < key(data[smallest]):
                smallest = i
        data[start], data[smallest] = data[smallest], data[start]
        if trace:
            print(f"  after pass {pass_number} (min={data[start]}): {data}")
    return data