"""Phase 3 Step 1: combine the starter CSVs into one flat file, one row per loan.

Run from the project root:  python sql/build_flat.py
"""

import csv
from pathlib import Path

DATA = Path("data")  # change this if your starter CSVs live somewhere else
OUT = Path("library_flat.csv")

COLUMNS = [
    "loan_id", "member_name", "email", "membership_type", "item_title",
    "authors", "isbn", "category", "parent_category", "pages", "price",
    "issue_date", "due_date", "return_date", "fine", "fine_paid",
]


def read_rows(name):
    with open(DATA / name, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


members = {row["member_id"]: row for row in read_rows("members.csv")}
books = {row["isbn"]: row for row in read_rows("books.csv")}
fines = {row["loan_id"]: row for row in read_rows("fines.csv")}

flat_rows = []
for loan in read_rows("loans.csv"):
    member = members[loan["member_id"]]
    book = books[loan["isbn"]]
    fine = fines.get(loan["loan_id"], {"amount": "", "paid": ""})  # no fine: blank
    flat_rows.append({
        "loan_id": loan["loan_id"],
        "member_name": member["name"],
        "email": member["email"],
        "membership_type": member["membership_type"],
        "item_title": book["title"],
        "authors": book["authors"],  # stays as "A;B" in one cell on purpose
        "isbn": loan["isbn"],
        "category": book["category"],
        "parent_category": book["parent_category"],
        "pages": book["pages"],
        "price": book["price"],
        "issue_date": loan["issue_date"],
        "due_date": loan["due_date"],
        "return_date": loan["return_date"],
        "fine": fine["amount"],
        "fine_paid": fine["paid"],
    })

with open(OUT, "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(flat_rows)

open_loans = sum(1 for row in flat_rows if row["return_date"] == "")
print(f"Wrote {OUT}: {len(flat_rows)} rows, {open_loans} open loans")