"""The unit of work: a group of changes that succeeds or fails as one.

`Library` only knows this small interface, so it never mentions a database. A
business operation (borrow, return, renew, ...) runs inside `transaction()`:
if it finishes, everything it changed is kept; if anything raises, none of it is.

`NullUnitOfWork` is used with the in-memory repositories: there is nothing to
undo there, so it just runs the block. The SQLite version lives in
`libraryhub.storage.unit_of_work`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from contextlib import AbstractContextManager


class UnitOfWork(ABC):
    @abstractmethod
    def transaction(self) -> AbstractContextManager[None]:
        """Use as `with unit_of_work.transaction():`.

        Leaving the block normally commits. An exception rolls back everything
        done inside the block and is then raised again, unchanged.
        """


class NullUnitOfWork(UnitOfWork):
    """For the in-memory repositories: no database, so no commit and no rollback."""

    @contextmanager
    def transaction(self) -> Iterator[None]:
        yield