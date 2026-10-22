import pytest
from libraryhub.members import Member, PremiumMember, RegularMember, StudentMember

# class, label, borrow limit, loan period in days, fine per day (the Rulebook table)
RULEBOOK_TABLE = [
    (StudentMember, "Student", 3, 14, 2),
    (RegularMember, "Regular", 5, 21, 5),
    (PremiumMember, "Premium", 10, 30, 3),
]


@pytest.mark.parametrize(("kind", "label", "limit", "days", "rate"), RULEBOOK_TABLE)
def test_member_answers_match_the_rulebook(kind, label, limit, days, rate):
    member = kind("M001", "Asha Raman", "asha@example.com")
    assert member.membership_label() == label
    assert member.borrow_limit() == limit  # R3
    assert member.loan_period_days() == days
    assert member.fine_per_day() == rate  # R5


def test_member_cannot_be_created_directly():
    with pytest.raises(TypeError):
        Member("M001", "Asha Raman", "asha@example.com")


@pytest.mark.parametrize("bad_email", ["", "asha.example.com", "asha"])
def test_email_without_at_is_rejected(bad_email):
    with pytest.raises(ValueError):
        StudentMember("M001", "Asha Raman", bad_email)


def test_changing_to_a_bad_email_raises_and_keeps_the_old_value():
    member = StudentMember("M001", "Asha Raman", "asha@example.com")
    with pytest.raises(ValueError):
        member.email = "nope"
    assert member.email == "asha@example.com"


def test_member_keeps_id_name_and_email():
    member = RegularMember("M002", "Rahul Mehta", "rahul@example.com")
    assert (member.member_id, member.name, member.email) == (
        "M002",
        "Rahul Mehta",
        "rahul@example.com",
    )


def test_str_reads_nicely():
    member = PremiumMember("M003", "Sneha Iyer", "sneha@example.com")
    assert str(member) == "Sneha Iyer (M003, Premium)"


def test_repr_shows_the_class_and_the_details():
    member = StudentMember("M004", "Karthik N", "karthik@example.com")
    assert repr(member) == (
        "StudentMember(member_id='M004', name='Karthik N', "
        "email='karthik@example.com')"
    )