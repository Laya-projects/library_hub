import pytest

from libraryhub.dsa.history import BorrowHistory
from libraryhub.errors import ValidationError


def make_history(*loan_ids):
    """Insert in the order given, so the LAST one given is the newest (the head)."""
    history = BorrowHistory()
    for loan_id in loan_ids:
        history.insert_at_head(loan_id)
    return history


# --- Insert at head and traversal --------------------------------------------


def test_a_new_history_is_empty():
    history = BorrowHistory()
    assert len(history) == 0
    assert list(history) == []
    assert str(history) == "None"


def test_insert_at_head_puts_the_newest_loan_first():
    history = make_history("L001", "L002", "L003")
    assert list(history) == ["L003", "L002", "L001"]
    assert len(history) == 3


def test_printing_matches_the_brief():
    assert str(make_history("L008", "L007", "L001")) == "L001 -> L007 -> L008 -> None"
    assert str(make_history("L006", "L003")) == "L003 -> L006 -> None"


def test_the_list_can_be_walked_twice():
    history = make_history("L001", "L002")
    assert list(history) == list(history) == ["L002", "L001"]


# --- Remove by loan ID -----------------------------------------------------------


def test_remove_from_the_middle():
    history = make_history("L001", "L002", "L003")
    assert history.remove("L002") is True
    assert list(history) == ["L003", "L001"]
    assert len(history) == 2


def test_remove_the_head():
    history = make_history("L001", "L002")
    assert history.remove("L002") is True
    assert list(history) == ["L001"]


def test_remove_the_last_node():
    history = make_history("L001", "L002")
    assert history.remove("L001") is True
    assert list(history) == ["L002"]


def test_remove_the_only_node_leaves_an_empty_history():
    history = make_history("L001")
    assert history.remove("L001") is True
    assert len(history) == 0
    assert str(history) == "None"


def test_remove_an_unknown_loan_changes_nothing():
    history = make_history("L001", "L002")
    assert history.remove("L999") is False
    assert list(history) == ["L002", "L001"]
    assert len(history) == 2


def test_remove_from_an_empty_history():
    assert BorrowHistory().remove("L001") is False


# --- Reverse ---------------------------------------------------------------------------


def test_reverse_puts_the_oldest_loan_first():
    history = make_history("L001", "L002", "L003")
    history.reverse()
    assert list(history) == ["L001", "L002", "L003"]
    assert len(history) == 3


def test_reverse_twice_gives_the_original_order():
    history = make_history("L001", "L002", "L003")
    history.reverse()
    history.reverse()
    assert list(history) == ["L003", "L002", "L001"]


@pytest.mark.parametrize("loan_ids", [[], ["L001"]])
def test_reverse_of_an_empty_or_single_history_is_unchanged(loan_ids):
    history = make_history(*loan_ids)
    history.reverse()
    assert list(history) == loan_ids


def test_insert_after_reverse_still_goes_to_the_head():
    history = make_history("L001", "L002")
    history.reverse()
    history.insert_at_head("L003")
    assert list(history) == ["L003", "L001", "L002"]


# --- n-th from the end -------------------------------------------------------------------


def test_second_from_the_end():
    history = make_history("L001", "L002", "L003", "L004")  # L004 -> ... -> L001
    assert history.nth_from_end(2) == "L002"


def test_first_from_the_end_is_the_oldest_loan():
    assert make_history("L001", "L002", "L003").nth_from_end(1) == "L001"


def test_n_equal_to_the_length_is_the_head():
    assert make_history("L001", "L002", "L003").nth_from_end(3) == "L003"


def test_n_longer_than_the_list_is_none():
    assert make_history("L001", "L002").nth_from_end(3) is None
    assert BorrowHistory().nth_from_end(1) is None


def test_n_below_one_is_refused():
    with pytest.raises(ValidationError):
        make_history("L001").nth_from_end(0)


# --- Long lists ------------------------------------------------------------------------------


def test_a_very_long_history_works_without_recursion():
    ids = [f"L{number:05d}" for number in range(10_000)]
    history = make_history(*ids)
    assert len(history) == 10_000
    assert list(history) == ids[::-1]
    history.reverse()
    assert list(history) == ids
    assert history.nth_from_end(1) == ids[-1]