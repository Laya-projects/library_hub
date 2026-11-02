"""The shapes of what the API sends back. FastAPI shows them in /docs."""

from __future__ import annotations

from pydantic import BaseModel


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