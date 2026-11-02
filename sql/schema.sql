-- LibraryHub Mini, Phase 3: schema (SQLite)
-- Run order: schema.sql first, then seed.sql.

PRAGMA foreign_keys = ON;

-- Limits for each kind of membership (3NF: they depend on the type, not the member)
CREATE TABLE membership_types (
    type         TEXT    PRIMARY KEY,
    borrow_limit INTEGER NOT NULL CHECK (borrow_limit > 0),
    loan_days    INTEGER NOT NULL CHECK (loan_days > 0),
    fine_per_day INTEGER NOT NULL CHECK (fine_per_day >= 0)
);

CREATE TABLE members (
    member_id       TEXT PRIMARY KEY,
    name            TEXT NOT NULL CHECK (length(trim(name)) > 0),
    email           TEXT NOT NULL UNIQUE CHECK (email LIKE '%_@_%'),
    membership_type TEXT NOT NULL
        REFERENCES membership_types (type) ON DELETE RESTRICT
);

-- Self-reference: a category may have a parent category (NULL when it has none)
CREATE TABLE categories (
    name   TEXT PRIMARY KEY,
    parent TEXT REFERENCES categories (name) ON DELETE RESTRICT,
    CHECK (parent IS NULL OR parent <> name)
);

CREATE TABLE items (
    isbn         TEXT PRIMARY KEY
        CHECK (length(isbn) = 13 AND isbn NOT GLOB '*[^0-9]*'),
    title        TEXT NOT NULL CHECK (length(trim(title)) > 0),
    item_type    TEXT NOT NULL CHECK (item_type IN ('Book', 'Magazine', 'Reference')),
    category     TEXT NOT NULL REFERENCES categories (name) ON DELETE RESTRICT,
    pages        INTEGER NOT NULL CHECK (pages > 0),
    price        INTEGER NOT NULL CHECK (price >= 0),
    total_copies INTEGER NOT NULL CHECK (total_copies >= 0)
);

CREATE TABLE authors (
    author_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL UNIQUE CHECK (length(trim(name)) > 0)
);

-- Junction table: one row for each (item, author) pair
CREATE TABLE item_authors (
    isbn      TEXT    NOT NULL REFERENCES items (isbn)        ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES authors (author_id) ON DELETE RESTRICT,
    PRIMARY KEY (isbn, author_id)
);

CREATE TABLE loans (
    loan_id     TEXT PRIMARY KEY,
    member_id   TEXT NOT NULL REFERENCES members (member_id) ON DELETE RESTRICT,
    isbn        TEXT NOT NULL REFERENCES items (isbn)        ON DELETE RESTRICT,
    issue_date  TEXT NOT NULL CHECK (date(issue_date) IS issue_date),
    due_date    TEXT NOT NULL CHECK (date(due_date) IS due_date),
    return_date TEXT CHECK (return_date IS NULL OR date(return_date) IS return_date),
    renewals    INTEGER NOT NULL DEFAULT 0 CHECK (renewals >= 0),
    CHECK (due_date >= issue_date),
    CHECK (return_date IS NULL OR return_date >= issue_date)
);

-- At most one fine for each loan, so the loan ID is also the key
CREATE TABLE fines (
    loan_id TEXT PRIMARY KEY REFERENCES loans (loan_id) ON DELETE CASCADE,
    amount  INTEGER NOT NULL CHECK (amount >= 0),
    paid    INTEGER NOT NULL DEFAULT 0 CHECK (paid IN (0, 1))
);

-- The waiting list: reservation_id grows over time, so it gives first come first served
CREATE TABLE reservations (
    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn           TEXT NOT NULL REFERENCES items (isbn)        ON DELETE CASCADE,
    member_id      TEXT NOT NULL REFERENCES members (member_id) ON DELETE CASCADE,
    UNIQUE (isbn, member_id)
);

-- No foreign keys on purpose: the log must survive whatever is deleted later
CREATE TABLE audit_log (
    log_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    action    TEXT NOT NULL,
    details   TEXT NOT NULL,
    logged_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);