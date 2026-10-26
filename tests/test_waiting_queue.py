import pytest

from libraryhub.dsa.waiting_queue import WaitingQueue
from libraryhub.errors import ValidationError


def make_queue(*member_ids):
    queue = WaitingQueue()
    for member_id in member_ids:
        queue.join(member_id)
    return queue


def test_a_new_queue_is_empty():
    queue = WaitingQueue()
    assert len(queue) == 0
    assert not queue
    assert queue.first() is None
    assert list(queue) == []


def test_join_returns_the_place_and_keeps_the_order_of_arrival():
    queue = WaitingQueue()
    assert queue.join("M001") == 1
    assert queue.join("M002") == 2
    assert queue.join("M003") == 3
    assert list(queue) == ["M001", "M002", "M003"]
    assert queue


def test_first_looks_at_the_front_without_removing_it():
    queue = make_queue("M001", "M002")
    assert queue.first() == "M001"
    assert len(queue) == 2


def test_pop_first_serves_strictly_first_come_first_served():
    queue = make_queue("M001", "M002", "M003")
    assert [queue.pop_first() for _ in range(3)] == ["M001", "M002", "M003"]
    assert queue.pop_first() is None


def test_a_long_queue_keeps_its_order():
    ids = [f"M{number:04d}" for number in range(1000)]
    queue = make_queue(*ids)
    assert [queue.pop_first() for _ in ids] == ids


def test_place_of_counts_from_one():
    queue = make_queue("M001", "M002")
    assert queue.place_of("M001") == 1
    assert queue.place_of("M002") == 2
    assert queue.place_of("M999") is None


def test_in_works_for_members_in_the_queue():
    queue = make_queue("M001")
    assert "M001" in queue
    assert "M002" not in queue


def test_leave_from_the_middle_closes_the_gap_and_returns_the_place():
    queue = make_queue("M001", "M002", "M003")
    assert queue.leave("M002") == 2
    assert list(queue) == ["M001", "M003"]
    assert queue.place_of("M003") == 2


def test_leave_when_not_queued_returns_none_and_changes_nothing():
    queue = make_queue("M001")
    assert queue.leave("M999") is None
    assert list(queue) == ["M001"]


def test_joining_twice_is_refused():
    queue = make_queue("M001")
    with pytest.raises(ValidationError, match="already in the waiting queue"):
        queue.join("M001")
    assert list(queue) == ["M001"]


def test_rejoin_gives_the_old_place_back():
    queue = make_queue("M001", "M003")
    queue.rejoin(2, "M002")
    assert list(queue) == ["M001", "M002", "M003"]


def test_rejoin_at_place_one_goes_to_the_front():
    queue = make_queue("M002")
    queue.rejoin(1, "M001")
    assert list(queue) == ["M001", "M002"]


def test_rejoin_refuses_place_zero_and_someone_already_queued():
    queue = make_queue("M001")
    with pytest.raises(ValidationError):
        queue.rejoin(0, "M002")
    with pytest.raises(ValidationError):
        queue.rejoin(1, "M001")
    assert list(queue) == ["M001"]
