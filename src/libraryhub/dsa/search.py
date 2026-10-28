"""Linear and binary search."""

from __future__ import annotations

from collections.abc import Sequence

from libraryhub.items import LibraryItem


def linear_search_by_title(items: Sequence[LibraryItem], title: str) -> int:
    """Index of the first item whose title matches (ignoring case), or -1."""
    wanted = title.casefold()
    for index, item in enumerate(items):
        if item.title.casefold() == wanted:
            return index
    return -1


def binary_search_counted(sorted_values: Sequence[str], target: str) -> tuple[int, int]:
    """(index or -1, number of comparisons). The values must already be sorted."""
    low, high = 0, len(sorted_values) - 1
    comparisons = 0
    while low <= high:
        middle = (low + high) // 2
        comparisons += 1  # one look at the middle value per pass
        if sorted_values[middle] == target:
            return middle, comparisons
        if sorted_values[middle] < target:
            low = middle + 1
        else:
            high = middle - 1
    return -1, comparisons


def binary_search(sorted_values: Sequence[str], target: str) -> int:
    return binary_search_counted(sorted_values, target)[0]