# ER diagram (draft)

Drawn with Mermaid (dbdiagram.io is not available on my work laptop). GitHub and
the VS Code Markdown preview draw it from the text below.

```mermaid
erDiagram
    MEMBERSHIP_TYPES |o--o{ MEMBERS : "sets limits for"
    CATEGORIES |o--o{ CATEGORIES : "is parent of"
    CATEGORIES ||--o{ ITEMS : "groups"
    ITEMS ||--|{ ITEM_AUTHORS : "is written by"
    AUTHORS ||--o{ ITEM_AUTHORS : "writes"
    MEMBERS ||--o{ LOANS : "borrows"
    ITEMS ||--o{ LOANS : "is lent in"
    LOANS ||--o| FINES : "may incur"
    MEMBERS ||--o{ RESERVATIONS : "waits in line"
    ITEMS ||--o{ RESERVATIONS : "is waited for"

    MEMBERSHIP_TYPES {
        text type_name PK "Student, Regular, Premium"
        int borrow_limit
        int loan_period_days
        int fine_per_day
    }

    MEMBERS {
        text member_id PK
        text name
        text email UK
        text membership_type FK
    }

    CATEGORIES {
        int category_id PK
        text name UK
        int parent_id FK "NULL for a top-level category"
    }

    ITEMS {
        text isbn PK "13 digits"
        text title
        text item_type "Book, Reference, Magazine"
        int category_id FK
        int pages
        int price
        int total_copies
    }

    AUTHORS {
        int author_id PK
        text name UK
    }

    ITEM_AUTHORS {
        text isbn PK, FK
        int author_id PK, FK
    }

    LOANS {
        text loan_id PK
        text member_id FK
        text isbn FK
        date issue_date
        date due_date
        date return_date "NULL while the loan is open"
        int renewals
    }

    FINES {
        text loan_id PK, FK "one fine per loan"
        int amount
        int paid "0 or 1"
    }

    RESERVATIONS {
        int reservation_id PK "order = place in the queue"
        text member_id FK
        text isbn FK
        datetime reserved_at
    }

    AUDIT_LOG {
        int audit_id PK
        text action "borrow, return, renew"
        text member_id
        text isbn
        datetime logged_at
    }

    UNDO_LOG {
        int undo_id PK "highest id = next to undo"
        text action "borrow or return"
        text loan_id
        text member_id
        text isbn
        int queue_position "NULL unless a borrow left the queue"
        int fine
    }
```

## How to read the lines

| Symbol | Meaning |
|---|---|
| `\|\|` | exactly one |
| `\|o` / `o\|` | zero or one |
| `o{` | zero or many |
| `\|{` | one or many |

Example: `MEMBERS ||--o{ LOANS` means one member has zero or many loans, and every
loan belongs to exactly one member.

## Cardinality of every relationship

| Relationship | Reads as |
|---|---|
| membership_types to members | a type has zero or many members, a member has exactly one type |
| categories to categories | a category has zero or many children and at most one parent |
| categories to items | a category groups zero or many items, an item has exactly one category |
| items to item_authors | an item has one or many author links |
| authors to item_authors | an author has zero or many author links (many-to-many with items) |
| members to loans | a member has zero or many loans, a loan has exactly one member |
| items to loans | an item is in zero or many loans, a loan has exactly one item |
| loans to fines | a loan has zero or one fine |
| members to reservations | a member has zero or many reservations |
| items to reservations | an item has zero or many reservations |

## Notes

- Availability is calculated, not stored (D1), so `ITEMS` has no `available_copies`.
- Every foreign key is `ON DELETE RESTRICT` (D2).
- `RESERVATIONS` and `UNDO_LOG` exist because the waiting list and undo history
  survive a restart (D4).
- `AUDIT_LOG` and `UNDO_LOG` have no foreign keys on purpose: a log must still be
  readable after what it describes has changed.
- This is a draft. Step 2 (normalisation) and Step 3 (`schema.sql`) may rename or
  move columns, and this diagram must be updated to match.