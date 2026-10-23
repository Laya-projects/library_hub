from datetime import date

import pytest

from libraryhub.errors import (
    BorrowLimitExceededError,
    DuplicateLoanError,
    InvalidISBNError,
    ItemNotAvailableError,
    ItemNotBorrowableError,
    ItemNotFoundError,
    LibraryError,
    LoanAlreadyReturnedError,
    LoanNotFoundError,
    MemberNotFoundError,
    RenewalNotAllowedError,
    UnpaidFinesError,
    ValidationError,
)

# (error object, exact line the brief's samples print)
SAMPLES = [
    (
        DuplicateLoanError("Asha Raman", "Wings of Fire"),
        "ERROR [R8]: Asha Raman already has a copy of 'Wings of Fire'.",
    ),
    (
        ItemNotBorrowableError("Encyclopaedia of Science"),
        (
            "ERROR [R1]: 'Encyclopaedia of Science' is a reference item "
            "and cannot be borrowed."
        ),
    ),
    (
        UnpaidFinesError("Karthik N", 120, 100),
        "ERROR [R4]: Karthik N has unpaid fines of ₹120 (limit ₹100).",
    ),
    (
        BorrowLimitExceededError("Asha Raman", 3, 3),
        "ERROR [R3]: Asha Raman already has 3 of 3 items on loan.",
    ),
    (
        MemberNotFoundError("M009"),
        "ERROR [MemberNotFoundError]: No member with ID M009.",
    ),
    (
        InvalidISBNError("123"),
        "ERROR [InvalidISBNError]: ISBN must be exactly 13 digits.",
    ),
    (
        ItemNotFoundError("9780000000999"),
        "ERROR [ItemNotFoundError]: No item with ISBN 9780000000999.",
    ),
    (
        RenewalNotAllowedError.limit_reached("Sapiens", 2),
        "ERROR [R6]: 'Sapiens' has already been renewed 2 times.",
    ),
    (
        RenewalNotAllowedError.magazine(),
        "ERROR [R2]: Magazines cannot be renewed.",
    ),
    (
        RenewalNotAllowedError.someone_waiting("Sapiens"),
        (
            "ERROR [R6]: 'Sapiens' cannot be renewed because another member "
            "is waiting."
        ),
    ),
]

ALL_ERRORS = [error for error, _ in SAMPLES] + [
    ItemNotAvailableError("The Alchemist"),
    ValidationError("title", "Title cannot be blank."),
    LoanNotFoundError("L999"),
    LoanAlreadyReturnedError("L004", date(2026, 9, 24)),
]


def name_of(error):
    return type(error).__name__


@pytest.mark.parametrize("error", ALL_ERRORS, ids=name_of)
def test_every_child_is_a_library_error(error):
    assert isinstance(error, LibraryError)
    assert isinstance(error, Exception)


@pytest.mark.parametrize("error", ALL_ERRORS, ids=name_of)
def test_catching_the_parent_catches_the_child(error):
    with pytest.raises(LibraryError) as caught:
        raise error
    assert caught.value is error


@pytest.mark.parametrize(
    ("error", "expected"),
    SAMPLES,
    ids=[name_of(error) for error, _ in SAMPLES],
)
def test_formatted_line_matches_the_sample(error, expected):
    assert error.formatted() == expected


def test_base_error_keeps_code_and_message():
    error = LibraryError("X1", "something broke")
    assert error.code == "X1"
    assert error.message == "something broke"
    assert error.formatted() == "ERROR [X1]: something broke"


@pytest.mark.parametrize("error", ALL_ERRORS, ids=name_of)
def test_str_of_an_error_is_its_message(error):
    assert str(error) == error.message


@pytest.mark.parametrize(
    "error",
    [
        InvalidISBNError("1"),
        ItemNotFoundError("1"),
        MemberNotFoundError("M1"),
        ValidationError("title", "Title cannot be blank."),
        LoanNotFoundError("L999"),
        LoanAlreadyReturnedError("L004", date(2026, 9, 24)),
    ],
    ids=name_of,
)
def test_non_rule_errors_use_their_class_name_as_code(error):
    assert error.code == type(error).__name__


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (ItemNotBorrowableError("t"), "R1"),
        (BorrowLimitExceededError("n", 3, 3), "R3"),
        (UnpaidFinesError("n", 120, 100), "R4"),
        (ItemNotAvailableError("t"), "R7"),
        (DuplicateLoanError("n", "t"), "R8"),
    ],
    ids=name_of,
)
def test_rule_errors_use_the_rule_number_as_code(error, code):
    assert error.code == code


def test_renewal_error_has_two_codes():
    assert RenewalNotAllowedError.magazine().code == "R2"
    assert RenewalNotAllowedError.limit_reached("Sapiens", 2).code == "R6"
    assert RenewalNotAllowedError.someone_waiting("Sapiens").code == "R6"


def test_errors_keep_their_raw_data():
    error = UnpaidFinesError("Karthik N", 120, 100)
    assert (error.member_name, error.unpaid, error.limit) == ("Karthik N", 120, 100)


def test_not_available_message_starts_the_waiting_list_prompt():
    # The menu prints this message, then adds " Join the waiting list? (y/n): ".
    error = ItemNotAvailableError("The Alchemist")
    assert error.message == "No copies of 'The Alchemist' are available."


@pytest.mark.parametrize(
    ("times", "expected"),
    [
        (1, "'Sapiens' has already been renewed 1 time."),
        (2, "'Sapiens' has already been renewed 2 times."),
    ],
)
def test_limit_reached_message_uses_singular_or_plural(times, expected):
    assert RenewalNotAllowedError.limit_reached("Sapiens", times).message == expected


def test_validation_error_line_and_field():
    error = ValidationError("title", "Title cannot be blank.")
    assert error.formatted() == "ERROR [ValidationError]: Title cannot be blank."
    assert error.field == "title"


def test_loan_errors_lines():
    assert LoanNotFoundError("L999").formatted() == (
        "ERROR [LoanNotFoundError]: No loan with ID L999."
    )
    assert LoanAlreadyReturnedError("L004", date(2026, 9, 24)).formatted() == (
        "ERROR [LoanAlreadyReturnedError]: Loan L004 was already returned "
        "on 2026-09-24."
    )