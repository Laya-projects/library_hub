"""Audit trail for the library.

Records who did what and when, without Library having to read the system clock
or manage audit logic inside core domain methods.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import TYPE_CHECKING, Any, Concatenate, ParamSpec, Protocol, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterator

P = ParamSpec("P")
R = TypeVar("R")


class SupportsAudit(Protocol):
    """An object that owns an AuditLog."""

    audit_log: AuditLog


T = TypeVar("T", bound=SupportsAudit)


@dataclass(frozen=True)
class AuditEntry:
    time: datetime
    action: str
    member_id: str
    isbn: str


class AuditLog:
    """Holds audit entries for a Library instance."""

    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self.clock: Callable[[], datetime] = clock if clock is not None else datetime.now
        self.entries: list[AuditEntry] = []

    def record(self, action: str, member_id: str, isbn: str) -> AuditEntry:
        entry = AuditEntry(
            time=self.clock(),
            action=action,
            member_id=member_id,
            isbn=isbn,
        )
        self.entries.append(entry)
        return entry

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self) -> Iterator[AuditEntry]:
        return iter(self.entries)


def _extract_audit_targets(result: Any) -> tuple[str, str]:
    """Extract (member_id, isbn) from a result object (Loan, ReturnResult, RenewResult)."""
    if hasattr(result, "loan"):
        loan = result.loan
        return str(loan.member_id), str(loan.isbn)
    if hasattr(result, "member_id") and hasattr(result, "isbn"):
        return str(result.member_id), str(result.isbn)
    raise TypeError(f"Cannot extract member_id and isbn from {type(result).__name__}")


def audit(
    action: str,
) -> Callable[[Callable[Concatenate[T, P], R]], Callable[Concatenate[T, P], R]]:
    """Decorator factory recording an audit entry on successful method execution."""

    def decorator(
        method: Callable[Concatenate[T, P], R],
    ) -> Callable[Concatenate[T, P], R]:
        @wraps(method)
        def wrapper(self: T, *args: P.args, **kwargs: P.kwargs) -> R:
            result = method(self, *args, **kwargs)
            member_id, isbn = _extract_audit_targets(result)
            self.audit_log.record(action, member_id, isbn)
            return result

        return wrapper

    return decorator
