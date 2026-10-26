"""A first-come, first-served waiting queue of member IDs (R7).

The members are kept in a `collections.deque`, so the front can be taken in
O(1). A plain list would need `pop(0)`, which moves every other entry one step
(O(n)). Places are numbered from 1, the way a member hears them: "#1" is first.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from libraryhub.errors import ValidationError

if TYPE_CHECKING:
    from collections.abc import Iterator


class WaitingQueue:
    """Member IDs in order of arrival. Nobody can be in the queue twice."""

    def __init__(self) -> None:
        self._ids: deque[str] = deque()

    # --- Looking -------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._ids)  # also makes an empty queue falsy

    def __iter__(self) -> Iterator[str]:
        return iter(self._ids)  # first in line first

    def __contains__(self, member_id: object) -> bool:
        return member_id in self._ids

    def first(self) -> str | None:
        """The member at the front, or None. The queue does not change. O(1)."""
        return self._ids[0] if self._ids else None

    def place_of(self, member_id: str) -> int | None:
        """The place of a member (1 = first), or None if not queued. O(n)."""
        for place, queued_id in enumerate(self._ids, start=1):
            if queued_id == member_id:
                return place
        return None

    # --- Changing ------------------------------------------------------------

    def join(self, member_id: str) -> int:
        """Join at the back and return the place. O(1) apart from the check."""
        self._refuse_if_queued(member_id)
        self._ids.append(member_id)
        return len(self._ids)

    def pop_first(self) -> str | None:
        """Serve the member at the front, or None if nobody waits. O(1)."""
        return self._ids.popleft() if self._ids else None

    def leave(self, member_id: str) -> int | None:
        """Leave from any place. Returns the place they had, or None. O(n).

        Needed because a member whose place fits a free copy may borrow without
        being first (D8), so the person leaving is not always at the front.
        """
        place = self.place_of(member_id)
        if place is not None:
            del self._ids[place - 1]
        return place

    def rejoin(self, place: int, member_id: str) -> None:
        """Put a member back at `place` (1 = first). Used to undo a borrow."""
        if place < 1:
            raise ValidationError("waiting_list", "A place in the queue starts at 1.")
        self._refuse_if_queued(member_id)
        self._ids.insert(place - 1, member_id)

    def _refuse_if_queued(self, member_id: str) -> None:
        if member_id in self._ids:
            raise ValidationError(
                "waiting_list", f"{member_id} is already in the waiting queue."
            )