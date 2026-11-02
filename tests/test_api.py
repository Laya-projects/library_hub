"""The API tests. They run on the in-memory world, so no database is needed."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from api.main import create_app

TODAY = date(2026, 10, 12)


@pytest.fixture
def client(library_world):
    return TestClient(create_app(library_world.library, TODAY))


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