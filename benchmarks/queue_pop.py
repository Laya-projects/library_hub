"""Drain 100,000 entries from the front: list.pop(0) against deque.popleft()."""

from collections import deque

from libraryhub.dsa.timing import median_ms_with_setup

N = 100_000


def drain_list(items):
    while items:
        items.pop(0)  # shifts every remaining item one place left


def drain_deque(items):
    while items:
        items.popleft()  # just moves the front pointer


def main():
    list_ms = median_ms_with_setup(lambda: list(range(N)), drain_list, runs=3)
    deque_ms = median_ms_with_setup(lambda: deque(range(N)), drain_deque, runs=3)
    print("| structure | time to remove 100,000 entries from the front (ms) |")
    print("|---|---|")
    print(f"| list.pop(0) | {list_ms:,.1f} |")
    print(f"| deque.popleft() | {deque_ms:,.1f} |")
    print(f"\nlist is {list_ms / deque_ms:,.0f}x slower")


if __name__ == "__main__":
    main()