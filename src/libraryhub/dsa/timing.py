"""Small timing helper: the median of several runs, in milliseconds."""

from __future__ import annotations

import statistics
import time
from collections.abc import Callable


def median_ms(action: Callable[[], object], runs: int = 7) -> float:
    """Time action() several times and return the median. One run is noise."""
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        action()
        times.append((time.perf_counter() - start) * 1000)
    return statistics.median(times)

from typing import TypeVar

S = TypeVar("S")


def median_ms_with_setup(
    setup: Callable[[], S], action: Callable[[S], object], runs: int = 7
) -> float:
    """Like median_ms, but each run gets a fresh state that is not timed."""
    times = []
    for _ in range(runs):
        state = setup()  # not timed
        start = time.perf_counter()
        action(state)
        times.append((time.perf_counter() - start) * 1000)
    return statistics.median(times)