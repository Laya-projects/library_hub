from datetime import date

import pytest

from libraryhub.main import DATA_DIR, build_library, main, parse_today


def test_today_comes_from_the_environment():
    assert parse_today({"TODAY": "2026-10-12"}) == date(2026, 10, 12)


def test_today_is_stripped():
    assert parse_today({"TODAY": " 2026-10-12 "}) == date(2026, 10, 12)


def test_today_defaults_to_the_real_date_when_missing_or_blank():
    assert parse_today({}) == date.today()
    assert parse_today({"TODAY": ""}) == date.today()


@pytest.mark.parametrize("bad", ["12-10-2026", "tomorrow", "2026-13-01", "2026-02-30"])
def test_bad_today_raises_a_clear_error(bad):
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        parse_today({"TODAY": bad})


def test_build_library_loads_the_csv_data():
    library = build_library(DATA_DIR)
    assert len(library.list_items()) == 7
    assert library.get_member("M001").name == "Asha Raman"


def test_main_with_a_bad_today_prints_an_error_and_returns_2(capsys):
    assert main({"TODAY": "nope"}) == 2
    assert capsys.readouterr().out.startswith("ERROR: TODAY must look like")


def test_main_runs_the_menu_and_exits_on_zero(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)  # the log file lands here, not in the project
    monkeypatch.setattr("builtins.input", lambda prompt: "0")
    assert main({"TODAY": "2026-10-12"}) == 0
    out = capsys.readouterr().out
    assert "today is 2026-10-12" in out
    assert "=== LibraryHub Mini ===" in out