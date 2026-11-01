"""THROWAWAY: the SQL injection experiment (brief 3.8). Never copy search_unsafe.

Keep this file OUT of src/: the wrap-up check looks for SQL built from text in
the program's code, and search_unsafe is built that way on purpose.

Run it from the project folder, as a module:

    python -m experiments.injection_demo

It prints the four results of the brief, then one extra attack, and saves the
same text to docs/injection_evidence.txt.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from libraryhub.main import DATA_DIR, build_sqlite_library

if TYPE_CHECKING:
    import sqlite3

    from libraryhub.storage.database import Database

EVIDENCE_FILE = DATA_DIR.parent / "docs" / "injection_evidence.txt"
ATTACK = "' OR '1'='1"
LEAK = "' UNION SELECT member_id, email FROM members --"  # the extra attack


def search_unsafe(db: Database, text: str) -> tuple[str, list[sqlite3.Row]]:
    """DO NOT COPY. The text is pasted into the SQL, so it can change the query."""
    sql = f"SELECT isbn, title FROM items WHERE title LIKE '%{text}%'"
    return sql, db.fetch_all(sql)


def search_safe(db: Database, text: str) -> tuple[str, list[sqlite3.Row]]:
    """The text travels as a parameter: it is data, and is never read as SQL."""
    sql = "SELECT isbn, title FROM items WHERE title LIKE ?"
    return sql, db.fetch_all(sql, (f"%{text}%",))


def rows_text(count: int) -> str:
    return f"{count} row" if count == 1 else f"{count} rows"


def run(db: Database) -> list[str]:
    lines: list[str] = []

    def probe(name: str, search, text: str, note: str = "") -> None:
        sql, rows = search(db, text)
        call = f'{name}("{text}")'
        lines.append(f"{call:<33}-> {rows_text(len(rows))}{note}")
        lines.append(f"    SQL sent: {sql}")

    probe("search_unsafe", search_unsafe, "Python")
    probe("search_unsafe", search_unsafe, ATTACK, "   (every item leaked)")
    probe("search_safe", search_safe, ATTACK)
    probe("search_safe", search_safe, "Python")

    lines.append("")
    lines.append("Extra: the same hole can read a table the search never meant to show.")
    _, rows = search_unsafe(db, LEAK)
    emails = [row["title"] for row in rows if "@" in str(row["title"])]
    lines.append(f'search_unsafe("{LEAK}")')
    lines.append(f"    -> {rows_text(len(rows))}, of which {len(emails)} are member emails:")
    lines.extend(f"       {email}" for email in emails)
    _, rows = search_safe(db, LEAK)
    lines.append(f'search_safe("{LEAK}")')
    lines.append(f"    -> {rows_text(len(rows))}")
    return lines


def main() -> None:
    _, database = build_sqlite_library(":memory:")  # a fresh database with the 7 items
    try:
        lines = run(database)
    finally:
        database.close()
    text = "\n".join(lines)
    print(text)
    EVIDENCE_FILE.parent.mkdir(exist_ok=True)
    EVIDENCE_FILE.write_text(text + "\n", encoding="utf-8")
    print(f"\nSaved to {EVIDENCE_FILE}")


if __name__ == "__main__":
    main()