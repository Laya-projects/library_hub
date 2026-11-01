"""The real program is safe against SQL injection: what you type is data, never SQL."""

import pytest

ATTACKS = [
    "' OR '1'='1",
    "'; DROP TABLE items; --",
    "' UNION SELECT member_id, email FROM members --",
]


@pytest.mark.parametrize("attack", ATTACKS)
def test_a_search_that_looks_like_sql_is_just_text(library_world, attack):
    assert library_world.library.search_items(attack) == []


@pytest.mark.parametrize("attack", ATTACKS)
def test_a_lookup_by_a_key_that_looks_like_sql_finds_nothing(library_world, attack):
    assert library_world.items.get(attack) is None
    assert library_world.members.get(attack) is None
    assert library_world.loans.get(attack) is None
    assert library_world.loans.list_for_member(attack) == []
    assert library_world.loans.list_for_isbn(attack) == []


def test_the_tables_and_their_rows_are_untouched_after_the_attacks(library_world):
    for attack in ATTACKS:
        library_world.library.search_items(attack)
        library_world.items.get(attack)
        library_world.members.get(attack)
    assert library_world.items.count() == 7
    assert library_world.members.count() == 5
    assert len(library_world.loans.list_all()) == 10