from libraryhub.dsa.fake_books import load_fake_library, make_fake_books


def test_makes_the_number_of_books_asked_for():
    assert len(make_fake_books(1000)) == 1000


def test_zero_books_is_an_empty_list():
    assert make_fake_books(0) == []


def test_isbns_are_unique_and_thirteen_digits():
    isbns = [book.isbn for book in make_fake_books(1000)]
    assert len(set(isbns)) == 1000
    assert all(len(isbn) == 13 and isbn.isdigit() for isbn in isbns)


def test_the_same_seed_gives_the_same_titles():
    first = [book.title for book in make_fake_books(200, seed=7)]
    second = [book.title for book in make_fake_books(200, seed=7)]
    assert first == second


def test_a_different_seed_gives_different_titles():
    first = [book.title for book in make_fake_books(200, seed=1)]
    second = [book.title for book in make_fake_books(200, seed=2)]
    assert first != second


def test_pages_price_and_copies_are_in_range():
    for book in make_fake_books(500):
        assert 50 <= book.pages <= 1200
        assert 100 <= book.price <= 1500
        assert 1 <= book.total_copies <= 3


def test_load_fake_library_holds_all_the_books():
    library = load_fake_library(1000)
    assert len(library.list_items()) == 1000


def test_fake_books_do_not_clash_with_the_starter_isbns():
    starter = {f"97800000000{n}" for n in ("11", "28", "35", "42", "59", "66", "73")}
    assert not starter & {book.isbn for book in make_fake_books(1000)}