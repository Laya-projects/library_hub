"""The shapes of what the API sends back. FastAPI shows them in /docs."""

from __future__ import annotations

from pydantic import BaseModel

from typing import Literal

class BookOut(BaseModel):
    isbn: str
    title: str
    authors: list[str]
    category: str
    item_type: str
    available: int
    total: int
    pages: int


class MemberOut(BaseModel):
    member_id: str
    name: str
    membership_type: str
    max_items: int


class LoanLineOut(BaseModel):
    loan_id: str
    title: str
    due_date: str
    days_overdue: int


class MemberLoansOut(BaseModel):
    member: str
    membership_type: str
    max_items: int
    unpaid_fines: int
    active: list[LoanLineOut]


# --- Requests (A2) ---------------------------------------------------------


class LoanIn(BaseModel):
    member_id: str
    isbn: str  # plain str on purpose: R9 is checked by Library, not by Pydantic


class ReservationIn(BaseModel):
    member_id: str
    isbn: str

class BookIn(BaseModel):
    isbn: str  # plain str: R9 is checked by the item class, not by Pydantic
    title: str
    copies: int
    authors: list[str] = []
    item_type: Literal["Book", "Magazine", "Reference"] = "Book"
    category: str = "General"
    parent_category: str | None = None
    pages: int = 1
    price: int = 0

# --- Responses of the write endpoints (A2) ----------------------------------


class LoanCreatedOut(BaseModel):
    loan_id: str
    due_date: str


class ReturnOut(BaseModel):
    loan_id: str
    days_late: int
    fine: int
    next_in_waiting_list: str | None


class ReservationOut(BaseModel):
    position: int