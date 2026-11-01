"""The database connection. It owns setup and transactions, and nothing else.

Every query in the program goes through `execute`, `fetch_one` or `fetch_all`,
and every value goes in the `params` tuple. SQL text is never built from data.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from libraryhub.members import PremiumMember, RegularMember, StudentMember

if TYPE_CHECKING:
    from collections.abc import Iterator

# src/libraryhub/storage/database.py -> the project root is three folders up.
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "sql" / "schema.sql"

# The membership limits live in the member classes. The table is filled from
# them, so the numbers are written in one place only.
_MEMBER_CLASSES = (StudentMember, RegularMember, PremiumMember)
from libraryhub.unit_of_work import UnitOfWork


class Database(UnitOfWork):
    def __init__(
        self,
        path: str | Path = ":memory:",
        schema_path: Path = SCHEMA_PATH,
    ) -> None:
        # isolation_level=None: Python never opens a transaction by itself, so
        # BEGIN, COMMIT and ROLLBACK below are the only ones (as in tx_demo.sql).
        self._connection = sqlite3.connect(str(path), isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._depth = 0  # how many transaction() blocks are open right now
        self._create_tables_if_missing(schema_path)
        self._fill_membership_types()

    # --- Setup ---------------------------------------------------------------

    def _create_tables_if_missing(self, schema_path: Path) -> None:
        exists = self.fetch_one(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'loans'"
        )
        if exists is None:
            self._connection.executescript(schema_path.read_text(encoding="utf-8"))

    def _fill_membership_types(self) -> None:
        for member_class in _MEMBER_CLASSES:
            sample = member_class("M000", "Sample", "sample@example.com")
            self.execute(
                "INSERT OR IGNORE INTO membership_types "
                "(type, borrow_limit, loan_days, fine_per_day) VALUES (?, ?, ?, ?)",
                (
                    sample.membership_label(),
                    sample.borrow_limit(),
                    sample.loan_period_days(),
                    sample.fine_per_day(),
                ),
            )

    # --- Running SQL: values always travel in `params` -------------------------

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Cursor:
        return self._connection.execute(sql, params)

    def fetch_one(
        self, sql: str, params: tuple[object, ...] = ()
    ) -> sqlite3.Row | None:
        row: sqlite3.Row | None = self._connection.execute(sql, params).fetchone()
        return row

    def fetch_all(self, sql: str, params: tuple[object, ...] = ()) -> list[sqlite3.Row]:
        return self._connection.execute(sql, params).fetchall()

    # --- Transactions ------------------------------------------------------------

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Commit when the block ends normally, roll back when it raises.

        Blocks can be nested. The outermost one is the real transaction; inner
        ones are savepoints, so an inner failure that is caught undoes only the
        inner part, and the outer block carries on.
        """
        outermost = self._depth == 0
        savepoint = f"unit_{self._depth}"
        self._connection.execute("BEGIN" if outermost else f"SAVEPOINT {savepoint}")
        self._depth += 1
        try:
            yield
        except BaseException:
            self._depth -= 1
            if outermost:
                self._connection.execute("ROLLBACK")
            else:
                self._connection.execute(f"ROLLBACK TO {savepoint}")
                self._connection.execute(f"RELEASE {savepoint}")
            raise
        self._depth -= 1
        self._connection.execute("COMMIT" if outermost else f"RELEASE {savepoint}")

    @property
    def in_transaction(self) -> bool:
        return self._connection.in_transaction    

    def close(self) -> None:
        self._connection.close()