"""The persistence check of the brief (3.7): borrow, close, reopen, still there."""

from datetime import date

from libraryhub.main import build_sqlite_library, main

TODAY = date(2026, 10, 12)
WINGS = "9780000000011"
ALCHEMIST = "9780000000028"
BRIEF_LINE = "L011  Wings of Fire  2026-10-12  2026-10-26  On loan"


def run_program(monkeypatch, capsys, db_path, answers):
    """Run main() once with scripted answers and return what it printed."""
    remaining = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(remaining))
    environ = {"TODAY": "2026-10-12", "LIBRARY_DB": str(db_path)}
    assert main(environ) == 0
    return capsys.readouterr().out


def test_a_loan_survives_closing_and_reopening(tmp_path):
    db_path = tmp_path / "library.db"
    library, database = build_sqlite_library(db_path)
    loan = library.borrow("M001", WINGS, TODAY)
    assert loan.loan_id == "L011"
    database.close()

    reopened, database = build_sqlite_library(db_path)
    try:
        assert reopened.get_loan("L011").member_id == "M001"
        assert len(reopened.member_loans("M001", TODAY).lines) == 1
    finally:
        database.close()


def test_reopening_does_not_load_the_csv_files_a_second_time(tmp_path):
    db_path = tmp_path / "library.db"
    _, database = build_sqlite_library(db_path)
    database.close()

    library, database = build_sqlite_library(db_path)
    try:
        assert len(library.list_items()) == 7
        assert len(library._loans.list_all()) == 10  # not 20
    finally:
        database.close()


def test_loan_numbers_carry_on_after_a_restart(tmp_path):
    db_path = tmp_path / "library.db"
    library, database = build_sqlite_library(db_path)
    library.borrow("M001", WINGS, TODAY)  # L011
    database.close()

    library, database = build_sqlite_library(db_path)
    try:
        assert library.borrow("M003", WINGS, TODAY).loan_id == "L012"
    finally:
        database.close()


def test_the_menu_shows_the_loan_after_the_program_is_run_again(
    tmp_path, monkeypatch, capsys
):
    db_path = tmp_path / "library.db"
    first = run_program(monkeypatch, capsys, db_path, ["3", "M001", WINGS, "0"])
    assert "OK: Asha Raman borrowed 'Wings of Fire'. Due 2026-10-26." in first

    second = run_program(monkeypatch, capsys, db_path, ["7", "M001", "0"])
    assert "Loans for Asha Raman (Student: 3 items, 14 days, ₹2/day)" in second
    assert BRIEF_LINE in second
    assert "Active loans: 1 of 3" in second
    assert "Unpaid fines: ₹0" in second


def test_an_undone_borrow_is_gone_after_a_restart(tmp_path):
    db_path = tmp_path / "library.db"
    library, database = build_sqlite_library(db_path)
    library.borrow("M001", WINGS, TODAY)
    library.undo()
    database.close()

    library, database = build_sqlite_library(db_path)
    try:
        assert len(library.member_loans("M001", TODAY).lines) == 0
    finally:
        database.close()