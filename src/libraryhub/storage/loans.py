"""Loans and fines stored in SQLite. Same interfaces as the in-memory versions."""

from __future__ import annotations

import sqlite3
from datetime import date
from typing import TYPE_CHECKING

from libraryhub.errors import LoanNotFoundError, ValidationError
from libraryhub.loans import Fine, Loan
from libraryhub.repositories import FineRepository, LoanRepository

if TYPE_CHECKING:
    from libraryhub.storage.database import Database


def _date_or_none(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


class SqliteLoanRepository(LoanRepository):
    def __init__(self, db: Database) -> None:
        self._db = db
        # Loan numbers come from a counter in memory. Building the stored loans
        # moves that counter past the highest stored ID, so after a restart the
        # next new loan is L012 and not L001 again.
        self.list_all()

    def add(self, loan: Loan) -> None:
        try:
            self._db.execute(
                """
                INSERT INTO loans (
                    loan_id, member_id, isbn, issue_date, due_date,
                    return_date, renewals
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    loan.loan_id,
                    loan.member_id,
                    loan.isbn,
                    loan.issue_date.isoformat(),
                    loan.due_date.isoformat(),
                    _date_or_none(loan.return_date),
                    loan.renewals,
                ),
            )
        except sqlite3.IntegrityError as error:
            if "loans.loan_id" in str(error):  # the same message as Phase 1
                raise ValidationError(
                    "loan_id", f"A loan with ID {loan.loan_id} already exists."
                ) from error
            raise ValidationError(
                "loan", f"Loan {loan.loan_id} cannot be stored: {error}"
            ) from error

    def update(self, loan: Loan) -> None:
        """Save what can change after a loan is made: due date, return, renewals."""
        cursor = self._db.execute(
            """
            UPDATE loans SET due_date = ?, return_date = ?, renewals = ?
            WHERE loan_id = ?
            """,
            (
                loan.due_date.isoformat(),
                _date_or_none(loan.return_date),
                loan.renewals,
                loan.loan_id,
            ),
        )
        if cursor.rowcount == 0:
            raise LoanNotFoundError(loan.loan_id)

    def remove(self, loan_id: str) -> None:
        cursor = self._db.execute("DELETE FROM loans WHERE loan_id = ?", (loan_id,))
        if cursor.rowcount == 0:
            raise LoanNotFoundError(loan_id)

    def get(self, loan_id: str) -> Loan | None:
        row = self._db.fetch_one("SELECT * FROM loans WHERE loan_id = ?", (loan_id,))
        return None if row is None else self._build(row)

    def list_all(self) -> list[Loan]:
        rows = self._db.fetch_all("SELECT * FROM loans ORDER BY rowid")
        return [self._build(row) for row in rows]

    def list_open(self) -> list[Loan]:
        rows = self._db.fetch_all(
            "SELECT * FROM loans WHERE return_date IS NULL ORDER BY rowid"
        )
        return [self._build(row) for row in rows]

    def list_for_member(self, member_id: str) -> list[Loan]:
        rows = self._db.fetch_all(
            "SELECT * FROM loans WHERE member_id = ? ORDER BY rowid", (member_id,)
        )
        return [self._build(row) for row in rows]

    def list_for_isbn(self, isbn: str) -> list[Loan]:
        rows = self._db.fetch_all(
            "SELECT * FROM loans WHERE isbn = ? ORDER BY rowid", (isbn,)
        )
        return [self._build(row) for row in rows]

    @staticmethod
    def _build(row: sqlite3.Row) -> Loan:
        return_date = row["return_date"]
        return Loan(
            row["member_id"],
            row["isbn"],
            date.fromisoformat(row["issue_date"]),
            date.fromisoformat(row["due_date"]),
            loan_id=row["loan_id"],
            return_date=None
            if return_date is None
            else date.fromisoformat(return_date),
            renewals=row["renewals"],
        )


class SqliteFineRepository(FineRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    def add(self, fine: Fine) -> None:
        try:
            self._db.execute(
                "INSERT INTO fines (loan_id, amount, paid) VALUES (?, ?, ?)",
                (fine.loan_id, fine.amount, 1 if fine.paid else 0),
            )
        except sqlite3.IntegrityError as error:
            if "UNIQUE" in str(error):  # the same message as Phase 1
                raise ValidationError(
                    "loan_id", f"A fine for loan {fine.loan_id} already exists."
                ) from error
            raise ValidationError(
                "fine", f"Fine for loan {fine.loan_id} cannot be stored: {error}"
            ) from error

    def list_all(self) -> list[Fine]:
        rows = self._db.fetch_all("SELECT * FROM fines ORDER BY rowid")
        return [Fine(row["loan_id"], row["amount"], bool(row["paid"])) for row in rows]

    def remove_for_loan(self, loan_id: str) -> None:
        self._db.execute("DELETE FROM fines WHERE loan_id = ?", (loan_id,))