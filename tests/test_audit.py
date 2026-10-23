from dataclasses import FrozenInstanceError
from datetime import datetime
from types import SimpleNamespace

import pytest

from libraryhub.audit import AuditEntry, AuditLog, audit

FIXED_TIME = datetime(2026, 10, 12, 9, 30, 0)


def test_audit_entry_dataclass_fields():
    entry = AuditEntry(FIXED_TIME, "borrow", "M001", "9780000000011")
    assert entry.time == FIXED_TIME
    assert entry.action == "borrow"
    assert entry.member_id == "M001"
    assert entry.isbn == "9780000000011"


def test_audit_entry_is_immutable():
    entry = AuditEntry(FIXED_TIME, "borrow", "M001", "9780000000011")
    with pytest.raises(FrozenInstanceError):
        entry.action = "renew"  # type: ignore[misc]


def test_audit_log_record_and_custom_clock():
    log = AuditLog(clock=lambda: FIXED_TIME)
    entry = log.record("borrow", "M001", "9780000000011")
    assert entry.time == FIXED_TIME
    assert entry.action == "borrow"
    assert entry.member_id == "M001"
    assert entry.isbn == "9780000000011"
    assert len(log) == 1
    assert log.entries == [entry]
    assert list(log) == [entry]


def test_audit_log_clock_can_be_replaced():
    log = AuditLog()
    log.clock = lambda: FIXED_TIME
    entry = log.record("renew", "M002", "9780000000028")
    assert entry.time == FIXED_TIME


def test_audit_decorator_preserves_function_metadata():
    class Dummy:
        audit_log = AuditLog()

        @audit("borrow")
        def borrow(self, member_id: str, isbn: str):
            """Borrow an item."""
            return SimpleNamespace(member_id=member_id, isbn=isbn)

    assert Dummy.borrow.__name__ == "borrow"
    assert Dummy.borrow.__doc__ == "Borrow an item."


def test_audit_decorator_records_on_success():
    class Service:
        def __init__(self):
            self.audit_log = AuditLog(clock=lambda: FIXED_TIME)

        @audit("borrow")
        def borrow(self, member_id: str, isbn: str):
            return SimpleNamespace(member_id=member_id, isbn=isbn)

    srv = Service()
    res = srv.borrow("M001", "9780000000011")
    assert res.member_id == "M001"
    assert len(srv.audit_log) == 1
    entry = srv.audit_log.entries[0]
    assert entry.time == FIXED_TIME
    assert entry.action == "borrow"
    assert entry.member_id == "M001"
    assert entry.isbn == "9780000000011"


def test_audit_decorator_records_nothing_if_method_raises():
    class BrokenService:
        def __init__(self):
            self.audit_log = AuditLog(clock=lambda: FIXED_TIME)

        @audit("borrow")
        def borrow(self, member_id: str, isbn: str):
            raise ValueError("Borrow failed")

    srv = BrokenService()
    with pytest.raises(ValueError, match="Borrow failed"):
        srv.borrow("M001", "9780000000011")

    assert len(srv.audit_log) == 0


def test_audit_decorator_extracts_from_nested_loan_result():
    class Service:
        def __init__(self):
            self.audit_log = AuditLog(clock=lambda: FIXED_TIME)

        @audit("return")
        def return_item(self, loan_id: str):
            loan = SimpleNamespace(
                member_id="M002", isbn="9780000000028", loan_id=loan_id
            )
            return SimpleNamespace(loan=loan, days_late=0)

        @audit("renew")
        def renew(self, loan_id: str):
            loan = SimpleNamespace(
                member_id="M003", isbn="9780000000035", loan_id=loan_id
            )
            return SimpleNamespace(loan=loan, renewals=1)

    srv = Service()
    srv.return_item("L001")
    srv.renew("L002")

    assert len(srv.audit_log) == 2
    assert srv.audit_log.entries[0].action == "return"
    assert srv.audit_log.entries[0].member_id == "M002"
    assert srv.audit_log.entries[0].isbn == "9780000000028"

    assert srv.audit_log.entries[1].action == "renew"
    assert srv.audit_log.entries[1].member_id == "M003"
    assert srv.audit_log.entries[1].isbn == "9780000000035"


def test_audit_logs_are_independent_per_instance():
    class Service:
        def __init__(self):
            self.audit_log = AuditLog()

        @audit("borrow")
        def borrow(self, member_id: str, isbn: str):
            return SimpleNamespace(member_id=member_id, isbn=isbn)

    s1 = Service()
    s2 = Service()
    s1.borrow("M001", "9780000000011")

    assert len(s1.audit_log) == 1
    assert len(s2.audit_log) == 0


def test_audit_decorator_raises_if_audit_log_is_missing():
    class MissingLogService:
        @audit("borrow")
        def borrow(self, member_id: str, isbn: str):
            return SimpleNamespace(member_id=member_id, isbn=isbn)

    srv = MissingLogService()
    with pytest.raises(AttributeError):
        srv.borrow("M001", "9780000000011")

def test_audit_rejects_a_result_it_cannot_read():
    class Fake:
        audit_log = AuditLog()

        @audit("odd")
        def do_something(self):
            return 42  # has no loan, member_id or isbn

    with pytest.raises(TypeError, match="Cannot extract member_id and isbn"):
        Fake().do_something()