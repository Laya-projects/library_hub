"""Golden test: a whole session must match the saved transcript exactly."""

from datetime import date
from pathlib import Path

from libraryhub.menu import Menu

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
TODAY = date(2026, 10, 12)


def run_session(library, answers):
    """Run the menu like a terminal: each prompt and typed answer share a line."""
    transcript = []
    remaining = iter(answers)

    def fake_input(prompt):
        answer = next(remaining)
        transcript.append(prompt + answer)
        return answer

    Menu(library, TODAY, fake_input, transcript.append).run()
    return "\n".join(transcript)


def test_session_a_matches_the_golden_transcript(library_world):
    answers = ["1", "3", "M001", "9780000000011", "7", "M002", "8", "0"]
    expected = (GOLDEN_DIR / "session_a.txt").read_text(encoding="utf-8").rstrip("\n")
    assert run_session(library_world.library, answers) == expected