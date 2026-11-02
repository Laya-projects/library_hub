"""The API tests. They run on the in-memory world, so no database is needed."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from api.main import create_app

TODAY = date(2026, 10, 12)


@pytest.fixture
def client(library_world):
    # raise_server_exceptions=False lets the 500 handler answer instead of the test crashing
    return TestClient(
        create_app(library_world.library, TODAY), raise_server_exceptions=False
    )


def borrow(client, member, isbn):
    return client.post("/loans", json={"member_id": member, "isbn": isbn})


# --- Read endpoints (A1) ------------------------------------------------------


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_search_python_matches_the_brief_sample(client):
    response = client.get("/books", params={"q": "python", "sort": "title"})
    assert response.status_code == 200
    assert response.json() == [
        {
            "isbn": "9780000000042",
            "title": "Python Crash Course",
            "authors": ["Eric Matthes"],
            "category": "Programming",
            "item_type": "Book",
            "available": 1,
            "total": 2,
            "pages": 544,
        }
    ]


def test_search_with_no_match_is_an_empty_list(client):
    response = client.get("/books", params={"q": "zzz"})
    assert (response.status_code, response.json()) == (200, [])


def test_a_blank_search_lists_all_seven_books(client):
    assert len(client.get("/books").json()) == 7
    assert len(client.get("/books", params={"q": "   "}).json()) == 7


def test_default_order_is_by_title(client):
    titles = [book["title"] for book in client.get("/books").json()]
    assert titles == sorted(titles, key=str.casefold)


def test_sort_by_pages_is_smallest_first(client):
    pages = [book["pages"] for book in client.get("/books?sort=pages").json()]
    assert pages == sorted(pages)


def test_sort_by_category_groups_by_top_category(client):
    books = client.get("/books?sort=category").json()
    assert [b["title"] for b in books][:2] == ["Wings of Fire", "The Alchemist"]


def test_an_unknown_sort_is_refused(client):
    assert client.get("/books?sort=colour").status_code == 422


def test_category_filter_uses_the_top_category(client):
    books = client.get("/books", params={"category": "Technology"}).json()
    assert sorted(book["title"] for book in books) == [
        "Clean Code",
        "Python Crash Course",
    ]


def test_search_and_filter_work_together(client):
    books = client.get("/books", params={"q": "code", "category": "Technology"}).json()
    assert [book["title"] for book in books] == ["Clean Code"]


def test_one_book_by_isbn(client):
    book = client.get("/books/9780000000028").json()
    assert (book["title"], book["available"], book["total"]) == ("The Alchemist", 0, 1)


def test_one_book_unknown_isbn_404(client):
    r = client.get("/books/9780000000999")
    assert r.status_code == 404
    assert r.json() == {
        "error": "ItemNotFoundError",
        "message": "No item with ISBN 9780000000999.",
    }


def test_categories_are_the_top_level_names(client):
    assert client.get("/categories").json() == [
        "Biography",
        "Fiction",
        "History",
        "Magazines",
        "Reference",
        "Technology",
    ]


def test_members_for_the_navbar_picker(client):
    members = client.get("/members").json()
    assert len(members) == 5
    assert members[0] == {
        "member_id": "M001",
        "name": "Asha Raman",
        "membership_type": "Student",
        "max_items": 3,
    }


def test_member_loans_match_the_brief_sample(client):
    response = client.get("/members/M002/loans")
    assert response.status_code == 200
    assert response.json() == {
        "member": "Rahul Mehta",
        "membership_type": "Regular",
        "max_items": 5,
        "unpaid_fines": 0,
        "active": [
            {
                "loan_id": "L001",
                "title": "The Alchemist",
                "due_date": "2026-09-22",
                "days_overdue": 20,
            }
        ],
    }


# --- Write endpoints and error mapping (A2) -----------------------------------


def test_borrow_201(client):
    r = borrow(client, "M001", "9780000000011")
    assert r.status_code == 201
    assert r.json() == {"loan_id": "L011", "due_date": "2026-10-26"}


def test_r8_409(client):
    borrow(client, "M001", "9780000000011")
    r = borrow(client, "M001", "9780000000011")
    assert r.status_code == 409
    assert r.json() == {
        "error": "R8",
        "message": "Asha Raman already has a copy of 'Wings of Fire'.",
    }


def test_r4_409(client):
    r = borrow(client, "M004", "9780000000035")
    assert r.status_code == 409
    assert r.json() == {
        "error": "R4",
        "message": "Karthik N has unpaid fines of ₹120 (limit ₹100).",
    }


def test_r1_409(client):
    r = borrow(client, "M003", "9780000000066")
    assert r.status_code == 409
    assert r.json() == {
        "error": "R1",
        "message": "'Encyclopaedia of Science' is a reference item and cannot be borrowed.",
    }


def test_member_404(client):
    r = borrow(client, "M009", "9780000000011")
    assert r.status_code == 404
    assert r.json() == {
        "error": "MemberNotFoundError",
        "message": "No member with ID M009.",
    }


def test_isbn_422(client):
    r = borrow(client, "M001", "123")
    assert r.status_code == 422
    assert r.json() == {
        "error": "InvalidISBNError",
        "message": "ISBN must be exactly 13 digits.",
    }


def test_missing_field_same_shape(client):
    r = client.post("/loans", json={"member_id": "M001"})
    assert r.status_code == 422
    assert set(r.json()) == {"error", "message"}


def test_return_with_waiting_list(client):
    client.post("/reservations", json={"member_id": "M003", "isbn": "9780000000028"})
    r = client.post("/loans/L001/return")
    assert r.status_code == 200
    assert r.json() == {
        "loan_id": "L001",
        "days_late": 20,
        "fine": 100,
        "next_in_waiting_list": "Sneha Iyer",
    }


def test_return_twice_409(client):
    client.post("/loans/L001/return")
    r = client.post("/loans/L001/return")
    assert r.status_code == 409
    assert r.json()["error"] == "LoanAlreadyReturnedError"


def test_unknown_loan_404(client):
    assert client.post("/loans/L999/return").status_code == 404


def test_reserve_201_then_already_queued_409(client):
    first = client.post(
        "/reservations", json={"member_id": "M003", "isbn": "9780000000028"}
    )
    assert (first.status_code, first.json()) == (201, {"position": 1})
    again = client.post(
        "/reservations", json={"member_id": "M003", "isbn": "9780000000028"}
    )
    assert again.status_code == 409
    assert again.json()["error"] == "ValidationError"


def test_reserve_when_copy_available_409(client):
    r = client.post(
        "/reservations", json={"member_id": "M001", "isbn": "9780000000011"}
    )
    assert r.status_code == 409


def test_unexpected_error_is_500_and_hides_details(client, library_world, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("secret detail")

    monkeypatch.setattr(library_world.library, "borrow", boom)
    r = borrow(client, "M001", "9780000000011")
    assert r.status_code == 500
    assert "secret" not in r.text
    assert set(r.json()) == {"error", "message"}


# --- CORS (A3) ------------------------------------------------------------------


def test_cors_allows_the_react_origin(client):
    r = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_refuses_another_origin(client):
    r = client.get("/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in r.headers


def test_cors_preflight_for_post_loans(client):
    r = client.options(
        "/loans",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


# --- POST /books (A2) -------------------------------------------------------------


def add_book(client, **overrides):
    body = {"isbn": "9780000000099", "title": "Fluent Python", "copies": 2}
    body.update(overrides)
    return client.post("/books", json=body)


def test_add_book_201(client):
    r = add_book(client, authors=["Luciano Ramalho"], pages=800)
    assert r.status_code == 201
    book = r.json()
    assert (book["isbn"], book["title"], book["item_type"]) == (
        "9780000000099", "Fluent Python", "Book",
    )
    assert (book["available"], book["total"], book["pages"]) == (2, 2, 800)
    assert len(client.get("/books").json()) == 8


def test_add_reference_item(client):
    r = add_book(client, item_type="Reference")
    assert r.status_code == 201
    assert r.json()["item_type"] == "Reference"


def test_add_book_duplicate_isbn_409(client):
    r = add_book(client, isbn="9780000000011")
    assert r.status_code == 409
    assert r.json() == {
        "error": "ValidationError",
        "message": "An item with ISBN 9780000000011 already exists.",
    }


def test_add_book_zero_copies_422(client):
    r = add_book(client, copies=0)
    assert r.status_code == 422
    assert r.json()["message"] == "A new item needs at least 1 copy."


def test_add_book_blank_title_422(client):
    r = add_book(client, title="   ")
    assert r.status_code == 422
    assert r.json() == {"error": "ValidationError", "message": "Title cannot be blank."}


def test_add_book_bad_isbn_422(client):
    r = add_book(client, isbn="123")
    assert r.status_code == 422
    assert r.json() == {
        "error": "InvalidISBNError",
        "message": "ISBN must be exactly 13 digits.",
    }


def test_add_book_missing_title_same_shape(client):
    r = client.post("/books", json={"isbn": "9780000000099", "copies": 1})
    assert r.status_code == 422
    assert set(r.json()) == {"error", "message"}