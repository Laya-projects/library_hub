"""Items stored in SQLite. Same interface as the in-memory repository."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from libraryhub.csv_loader import ITEM_CLASSES
from libraryhub.errors import ValidationError
from libraryhub.repositories import ItemRepository

if TYPE_CHECKING:
    from libraryhub.items import LibraryItem
    from libraryhub.storage.database import Database


class SqliteItemRepository(ItemRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    # --- Reading ---------------------------------------------------------------

    def get(self, isbn: str) -> LibraryItem | None:
        row = self._db.fetch_one(
            """
            SELECT i.isbn, i.title, i.item_type, i.category,
                   c.parent AS parent_category, i.pages, i.price, i.total_copies
            FROM items AS i
            JOIN categories AS c ON c.name = i.category
            WHERE i.isbn = ?
            """,
            (isbn,),
        )
        if row is None:
            return None
        authors = self._db.fetch_all(
            """
            SELECT a.name
            FROM item_authors AS ia
            JOIN authors AS a ON a.author_id = ia.author_id
            WHERE ia.isbn = ?
            ORDER BY ia.rowid
            """,
            (isbn,),
        )
        return self._build(row, [author["name"] for author in authors])

    def list_all(self) -> list[LibraryItem]:
        """Every item in the order it was added (the catalogue order)."""
        rows = self._db.fetch_all(
            """
            SELECT i.isbn, i.title, i.item_type, i.category,
                   c.parent AS parent_category, i.pages, i.price, i.total_copies
            FROM items AS i
            JOIN categories AS c ON c.name = i.category
            ORDER BY i.rowid
            """
        )
        # One query for all authors, so listing does not cost one query per item.
        authors_by_isbn: dict[str, list[str]] = {}
        for pair in self._db.fetch_all(
            """
            SELECT ia.isbn, a.name
            FROM item_authors AS ia
            JOIN authors AS a ON a.author_id = ia.author_id
            ORDER BY ia.rowid
            """
        ):
            authors_by_isbn.setdefault(pair["isbn"], []).append(pair["name"])
        return [self._build(row, authors_by_isbn.get(row["isbn"], [])) for row in rows]

    def count(self) -> int:
        row = self._db.fetch_one("SELECT COUNT(*) AS n FROM items")
        return int(row["n"]) if row is not None else 0

    # --- Writing -----------------------------------------------------------------

    def add(self, item: LibraryItem) -> None:
        """Store an item with its categories and authors, all or nothing."""
        with self._db.transaction():
            self._add_categories(item)
            try:
                self._db.execute(
                    """
                    INSERT INTO items
                        (isbn, title, item_type, category, pages, price, total_copies)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.isbn,
                        item.title,
                        item.item_type().value,
                        item.category,
                        item.pages,
                        item.price,
                        item.total_copies,
                    ),
                )
            except sqlite3.IntegrityError as error:
                if "items.isbn" in str(error):  # the same message as Phase 1 (R9)
                    raise ValidationError(
                        "isbn", f"An item with ISBN {item.isbn} already exists."
                    ) from error
                raise ValidationError(
                    "item", f"Item cannot be stored: {error}"
                ) from error
            for name in item.authors:
                self._db.execute(
                    "INSERT OR IGNORE INTO authors (name) VALUES (?)", (name,)
                )
                self._db.execute(
                    """
                    INSERT OR IGNORE INTO item_authors (isbn, author_id)
                    SELECT ?, author_id FROM authors WHERE name = ?
                    """,
                    (item.isbn, name),
                )

    def _add_categories(self, item: LibraryItem) -> None:
        """The parent first, then the category that points to it."""
        if item.parent_category:
            self._db.execute(
                "INSERT OR IGNORE INTO categories (name, parent) VALUES (?, NULL)",
                (item.parent_category,),
            )
        self._db.execute(
            "INSERT OR IGNORE INTO categories (name, parent) VALUES (?, ?)",
            (item.category, item.parent_category or None),
        )

    # --- Turning a row back into an object -----------------------------------------

    @staticmethod
    def _build(row: sqlite3.Row, authors: list[str]) -> LibraryItem:
        item_class = ITEM_CLASSES[row["item_type"]]  # a dictionary, no if-chain
        return item_class(
            isbn=row["isbn"],
            title=row["title"],
            authors=authors,
            category=row["category"],
            parent_category=row["parent_category"],
            pages=row["pages"],
            price=row["price"],
            total_copies=row["total_copies"],
        )