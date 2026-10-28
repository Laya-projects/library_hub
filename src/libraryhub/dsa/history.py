"""A singly linked list of loan IDs: the borrowing history of one member.

Each node holds one loan ID and points to the next (older) one. New loans go in
at the head, so reading from the head shows the newest loan first. No array is
involved, so adding at the head never moves any other entry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from libraryhub.errors import ValidationError

if TYPE_CHECKING:
    from collections.abc import Iterator


class Node:
    """One link of the chain: a loan ID and the node after it."""

    __slots__ = ("loan_id", "next")

    def __init__(self, loan_id: str, next_node: Node | None = None) -> None:
        self.loan_id = loan_id
        self.next = next_node


class BorrowHistory:
    """Loan IDs from newest to oldest."""

    def __init__(self) -> None:
        self._head: Node | None = None
        self._size = 0

    # --- Looking -------------------------------------------------------------

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[str]:
        """Walk from the head: O(n). A loop, not recursion, so any length works."""
        node = self._head
        while node is not None:
            yield node.loan_id
            node = node.next

    def __str__(self) -> str:
        """'L001 -> L007 -> None', newest first. An empty history is 'None'."""
        return " -> ".join([*self, "None"])

    def nth_from_end(self, n: int) -> str | None:
        """The n-th loan ID counted from the end (1 = the last), or None.

        One pass with two pointers: the leader starts n steps ahead, so when it
        falls off the end the follower is exactly n from the end. O(n), no
        length needed.
        """
        if n < 1:
            raise ValidationError("history", "n must be 1 or more.")
        leader = self._head
        for _ in range(n):
            if leader is None:
                return None  # the list is shorter than n
            leader = leader.next
        follower = self._head
        while leader is not None and follower is not None:
            leader = leader.next
            follower = follower.next
        return follower.loan_id if follower is not None else None

    # --- Changing ------------------------------------------------------------

    def insert_at_head(self, loan_id: str) -> None:
        """Make this the newest loan. O(1)."""
        self._head = Node(loan_id, self._head)
        self._size += 1

    def remove(self, loan_id: str) -> bool:
        """Unlink the first node with this loan ID. False if there is none. O(n)."""
        previous: Node | None = None
        node = self._head
        while node is not None:
            if node.loan_id == loan_id:
                if previous is None:
                    self._head = node.next  # the head itself is removed
                else:
                    previous.next = node.next
                self._size -= 1
                return True
            previous, node = node, node.next
        return False

    def reverse(self) -> None:
        """Turn the list around in place, so the oldest comes first. O(n)."""
        previous: Node | None = None
        node = self._head
        while node is not None:
            following = node.next  # remember it before the link is turned
            node.next = previous
            previous = node
            node = following
        self._head = previous