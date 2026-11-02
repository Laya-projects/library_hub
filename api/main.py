"""The HTTP API in front of the Library. It calls Library methods and nothing else.

No rule (R1 to R10) is written here. The API turns a request into a Library call
and turns the answer into JSON.

    $env:TODAY="2026-10-12"; python -m uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations
from libraryhub.csv_loader import ITEM_CLASSES
import os
from contextlib import asynccontextmanager
from datetime import date
from typing import TYPE_CHECKING, Annotated, Literal

from fastapi import APIRouter, Depends, FastAPI, Request

from api.errors import register_error_handlers
from api.schemas import (
    BookIn,
    BookOut,
    LoanCreatedOut,
    LoanIn,
    LoanLineOut,
    MemberLoansOut,
    MemberOut,
    ReservationIn,
    ReservationOut,
    ReturnOut,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from libraryhub.items import LibraryItem
    from libraryhub.library import Library

from fastapi.middleware.cors import CORSMiddleware

TITLE = "LibraryHub Mini API"

# Every endpoint below is `async def` with no `await` inside. FastAPI then runs
# them all on one thread, one request at a time. The database has one SQLite
# connection that may only be used by the thread that made it, and this also
# means two borrows at the same moment are handled one after the other.
router = APIRouter()


# --- What the endpoints receive: the one Library and today's date --------------


def get_library(request: Request) -> Library:
    library: Library = request.app.state.library
    return library


def get_today(request: Request) -> date:
    today: date = request.app.state.today
    return today


LibraryDep = Annotated["Library", Depends(get_library)]
TodayDep = Annotated[date, Depends(get_today)]


# --- Turning Library objects into the JSON shapes -------------------------------


def top_category(item: LibraryItem) -> str:
    """The category shown in the filter: the parent when there is one."""
    return item.parent_category or item.category


def book_out(library: Library, item: LibraryItem) -> BookOut:
    return BookOut(
        isbn=item.isbn,
        title=item.title,
        authors=item.authors,
        category=item.category,
        item_type=item.item_type().value,
        available=library.available_copies(item.isbn),
        total=item.total_copies,
        pages=item.pages,
    )


# How each sort option orders books. A dictionary, so a new option is one line.
SORT_KEYS: dict[str, Callable[[LibraryItem], tuple[object, ...]]] = {
    "title": lambda item: (item.title.casefold(),),
    "pages": lambda item: (item.pages, item.title.casefold()),
    "category": lambda item: (top_category(item).casefold(), item.title.casefold()),
}


# --- Read endpoints ------------------------------------------------------------


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/books", response_model=list[BookOut])
async def list_books(
    library: LibraryDep,
    q: str = "",
    sort: Literal["title", "pages", "category"] = "title",
    category: str = "",
) -> list[BookOut]:
    # A blank search means "show everything" (Library.search_items refuses blank).
    items = library.search_items(q) if q.strip() else library.list_items()
    if category:
        items = [item for item in items if top_category(item) == category]
    items = sorted(items, key=SORT_KEYS[sort])
    return [book_out(library, item) for item in items]


@router.get("/books/{isbn}", response_model=BookOut)
async def get_book(isbn: str, library: LibraryDep) -> BookOut:
    return book_out(library, library.get_item(isbn))


@router.get("/categories", response_model=list[str])
async def list_categories(library: LibraryDep) -> list[str]:
    return sorted({top_category(item) for item in library.list_items()})


@router.get("/members", response_model=list[MemberOut])
async def list_members(library: LibraryDep) -> list[MemberOut]:
    return [
        MemberOut(
            member_id=member.member_id,
            name=member.name,
            membership_type=member.membership_label(),
            max_items=member.borrow_limit(),
        )
        for member in library.list_members()
    ]


@router.get("/members/{member_id}/loans", response_model=MemberLoansOut)
async def member_loans(
    member_id: str, library: LibraryDep, today: TodayDep
) -> MemberLoansOut:
    report = library.member_loans(member_id, today)
    return MemberLoansOut(
        member=report.member.name,
        membership_type=report.member.membership_label(),
        max_items=report.member.borrow_limit(),
        unpaid_fines=report.unpaid_fines,
        active=[
            LoanLineOut(
                loan_id=line.loan.loan_id,
                title=line.item.title,
                due_date=line.loan.due_date.isoformat(),
                days_overdue=line.days_late,
            )
            for line in report.lines
        ],
    )


# --- Write endpoints -------------------------------------------------------------


@router.post("/loans", status_code=201, response_model=LoanCreatedOut)
async def create_loan(
    body: LoanIn, library: LibraryDep, today: TodayDep
) -> LoanCreatedOut:
    loan = library.borrow(body.member_id, body.isbn, today)
    return LoanCreatedOut(loan_id=loan.loan_id, due_date=loan.due_date.isoformat())


@router.post("/loans/{loan_id}/return", response_model=ReturnOut)
async def return_loan(
    loan_id: str, library: LibraryDep, today: TodayDep
) -> ReturnOut:
    result = library.return_item(loan_id, today)
    return ReturnOut(
        loan_id=result.loan.loan_id,
        days_late=result.days_late,
        fine=result.fine,
        next_in_waiting_list=result.next_waiting.name if result.next_waiting else None,
    )


@router.post("/reservations", status_code=201, response_model=ReservationOut)
async def create_reservation(
    body: ReservationIn, library: LibraryDep
) -> ReservationOut:
    return ReservationOut(position=library.reserve(body.member_id, body.isbn))

@router.post("/books", status_code=201, response_model=BookOut)
async def add_book(body: BookIn, library: LibraryDep) -> BookOut:
    item_class = ITEM_CLASSES[body.item_type]
    item = item_class(
        isbn=body.isbn,
        title=body.title,
        authors=body.authors,
        category=body.category,
        parent_category=body.parent_category,
        pages=body.pages,
        price=body.price,
        total_copies=body.copies,
    )
    library.add_item(item)
    return book_out(library, item)

# --- Building the app ------------------------------------------------------------


def _open_library() -> tuple[Library, Callable[[], None]]:
    """Open the real database. Returns the Library and a function that closes it."""
    # Imported here so tests, which pass their own Library, never need the database.
    from libraryhub.main import build_sqlite_library

    path = os.environ.get("LIBRARYHUB_DB", "libraryhub.db")
    library, database = build_sqlite_library(path)  # adjust if yours returns more
    return library, database.close


@asynccontextmanager
async def _real_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Server start: read TODAY once, build one Library. Server stop: close it."""
    from libraryhub.main import parse_today

    app.state.today = parse_today(os.environ)
    app.state.library, close = _open_library()
    try:
        yield
    finally:
        close()


def create_app(library: Library | None = None, today: date | None = None) -> FastAPI:
    """Tests pass their own Library and date. The real server passes nothing."""
    if library is None:
        app = FastAPI(title=TITLE, lifespan=_real_lifespan)
    else:
        app = FastAPI(title=TITLE)
        app.state.library = library
        app.state.today = today if today is not None else date.today()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.environ.get("WEB_ORIGIN", "http://localhost:5173")],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(router)
    register_error_handlers(app)
    return app

app = create_app()