"""Run .sql files against a SQLite database and print what the SELECTs return.

Use it when you have no sqlite3 shell. From the project folder:

    python sql/run_sql.py library.db sql/schema.sql sql/seed.sql
    python sql/run_sql.py library.db sql/queries.sql
    python sql/run_sql.py :memory: sql/schema.sql sql/seed.sql sql/queries.sql

The files run in the order given. ":memory:" is a database that disappears when
the script ends, which is handy for trying things.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


def statements(script: str) -> Iterator[str]:
    """Split a script into complete SQL statements (a ; inside quotes is handled)."""
    buffer = ""
    for line in script.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            yield buffer.strip()
            buffer = ""
    rest = buffer.strip()  # a last statement the writer forgot to end with ;
    if any(line.strip() and not line.strip().startswith("--") for line in rest.splitlines()):
        yield rest


def show(cursor: sqlite3.Cursor) -> None:
    """Print a result as tab-separated lines, header first."""
    print("\t".join(column[0] for column in cursor.description))
    rows = cursor.fetchall()
    for row in rows:
        print("\t".join("NULL" if value is None else str(value) for value in row))
    print(f"({len(rows)} rows)\n")


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    database, *files = argv[1:]
    # isolation_level=None: the script's own BEGIN / COMMIT / ROLLBACK are obeyed.
    connection = sqlite3.connect(database, isolation_level=None)
    connection.execute("PRAGMA foreign_keys = ON")  # off by default in SQLite!
    for name in files:
        print(f"-- {name}")
        path = Path(name)
        if path.is_dir():
            print(f"ERROR: {name} is a folder, not a file.\n")
            continue
        try:
            with open(name, encoding="utf-8-sig") as sql_file:  # -sig: skips a BOM
                script = sql_file.read()
        except (OSError, UnicodeDecodeError) as error:
            print(f"ERROR: cannot read {name}: {error}\n")
            continue
        found = 0
        for statement in statements(script):
            found += 1
            try:
                cursor = connection.execute(statement)
            except sqlite3.Error as error:
                print(f"ERROR: {error}\n  in: {statement[:200]}\n")
                continue  # keep going, so a deliberate failure (tx_demo) is visible
            if cursor.description:  # only SELECTs have columns
                show(cursor)
        if found == 0:
            print("(no SQL statements found: is the file empty or not saved?)\n")
    connection.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))