# Normalisation write-up

## 1. The flat file

`library_flat.csv` has one row per loan (10 rows) and 16 columns. Member, item,
category and fine details are all copied onto every loan row.

## 2. Three anomalies in the flat file

### Update anomaly: the same fact is stored many times

Rahul Mehta's email `rahul@example.com` is on 3 rows (L001, L007, L008). Wings of
Fire's price `250` is also on 3 rows (L004, L008, L010). If Rahul changes his email
and I update only L001 and L007, the file says he has two different emails and
nothing shows which one is right. The fact should live in one place.

### Insert anomaly: a fact cannot exist without a loan

Divya Rao (M005) is a member but has never borrowed, so she has no row. The
Encyclopaedia of Science is in the catalogue but has never been borrowed, so it
has no row either. The key of this file is the loan ID, so to record either of
them I would have to invent a fake loan row with blank loan fields.

### Delete anomaly: removing a loan removes other facts

Sapiens appears on exactly one row, L003 (Sneha Iyer). Clean Code also appears
on exactly one row, L006. If L003 is deleted, the title, authors, category,
pages and price of Sapiens disappear from the file, even though the library
still owns the book. Deleting a loan should never delete a book.

## 3. What these anomalies tell me

Members, items and loans are three different things stored in one table. Each
should have its own table, linked by IDs. The next sections take the file to
1NF, 2NF and 3NF to do exactly that.


## 4. First normal form (1NF)

**What repeats inside a cell?** The `authors` column. L004, L008 and L010 (Wings of
Fire) hold `A.P.J. Abdul Kalam;Arun Tiwari` in one cell. 1NF needs one value per
cell, so a query cannot answer "which books did Arun Tiwari write?" without
splitting text.

**Before** (one row per loan, 10 rows):

| loan_id | item_title    | authors                          |
|---------|---------------|----------------------------------|
| L004    | Wings of Fire | A.P.J. Abdul Kalam;Arun Tiwari   |

**After** (one row per loan and author, 13 rows):

| loan_id | item_title    | author             |
|---------|---------------|--------------------|
| L004    | Wings of Fire | A.P.J. Abdul Kalam |
| L004    | Wings of Fire | Arun Tiwari        |

The key is now two columns: `(loan_id, author)`.

## 5. Second normal form (2NF)

2NF applies when the key has more than one column. A column breaks it if it
depends on only part of the key.

- `author` depends on the item (ISBN), not on the loan. It belongs with the item.
- Every other column (member, dates, fine, title, price...) depends on `loan_id`
  alone and has nothing to do with the author. So these are partial dependencies.

**Split:**

- `loans_flat(loan_id, member..., item..., dates, fine)` with key `loan_id`
- `item_authors(isbn, author)` with key `(isbn, author)`

## 6. Third normal form (3NF)

3NF removes columns that depend on another non-key column.

| Chain in the file | Meaning | New table |
|---|---|---|
| `loan_id -> member -> name, email, membership_type` | member facts depend on the member, not the loan | `members` |
| `membership_type -> borrow limit, loan days, fine per day` | limits depend on the type, not the member | `membership_types` |
| `loan_id -> isbn -> title, pages, price, category, item type, copies` | item facts depend on the ISBN | `items` |
| `category -> parent_category` | the parent depends on the category | `categories` (self-reference) |
| `author` as text, repeated per item | one author can write many items | `authors` + `item_authors` |
| `loan_id -> fine, fine_paid` | blank for 6 of 10 loans | `fines` |

## 7. Final tables

| Table | Key | Main columns |
|---|---|---|
| `membership_types` | `type` | borrow_limit, loan_days, fine_per_day |
| `members` | `member_id` | name, email (unique), membership_type -> membership_types |
| `categories` | `name` | parent -> categories (nullable) |
| `items` | `isbn` | title, item_type, category -> categories, pages, price, total_copies |
| `authors` | `author_id` | name |
| `item_authors` | `(isbn, author_id)` | links items and authors |
| `loans` | `loan_id` | member_id, isbn, issue_date, due_date, return_date |
| `fines` | `loan_id` | amount, paid |
| `reservations` | `reservation_id` | isbn, member_id, `UNIQUE (isbn, member_id)`. The ID gives first come, first served |
| `audit_log` | `log_id` | action, details, time |

`reservations` and `audit_log` do not come from the flat file. They are added for
the waiting list and the audit decorator.

**Counts to expect after loading:** 3 membership types, 5 members, 8 categories,
7 items, 7 authors, 10 loans, 4 fines.