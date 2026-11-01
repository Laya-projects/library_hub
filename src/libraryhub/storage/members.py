"""Members stored in SQLite. Same interface as the in-memory repository."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from libraryhub.csv_loader import MEMBER_CLASSES
from libraryhub.errors import ValidationError
from libraryhub.repositories import MemberRepository

if TYPE_CHECKING:
    from libraryhub.members import Member
    from libraryhub.storage.database import Database


class SqliteMemberRepository(MemberRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    def get(self, member_id: str) -> Member | None:
        row = self._db.fetch_one(
            "SELECT * FROM members WHERE member_id = ?", (member_id,)
        )
        return None if row is None else self._build(row)

    def add(self, member: Member) -> None:
        try:
            self._db.execute(
                """
                INSERT INTO members (member_id, name, email, membership_type)
                VALUES (?, ?, ?, ?)
                """,
                (
                    member.member_id,
                    member.name,
                    member.email,
                    member.membership_label(),
                ),
            )
        except sqlite3.IntegrityError as error:
            text = str(error)
            if "members.member_id" in text:  # the same message as Phase 1
                raise ValidationError(
                    "member_id", f"A member with ID {member.member_id} already exists."
                ) from error
            if "members.email" in text:
                raise ValidationError(
                    "email", f"A member with email {member.email} already exists."
                ) from error
            raise ValidationError(
                "member", f"Member cannot be stored: {text}"
            ) from error

    def list_all(self) -> list[Member]:
        """Every member in the order they were added."""
        rows = self._db.fetch_all("SELECT * FROM members ORDER BY rowid")
        return [self._build(row) for row in rows]

    def count(self) -> int:
        row = self._db.fetch_one("SELECT COUNT(*) AS n FROM members")
        return int(row["n"]) if row is not None else 0

    @staticmethod
    def _build(row: sqlite3.Row) -> Member:
        member_class = MEMBER_CLASSES[row["membership_type"]]
        return member_class(row["member_id"], row["name"], row["email"])