"""Library members: students, regular readers and premium members."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Member(ABC):
    """A library member.

    Every kind of member answers the same four questions with its own values,
    so the rest of the code never has to ask "what type are you?".
    """

    def __init__(self, member_id: str, name: str, email: str) -> None:
        self.member_id = member_id
        self.name = name
        self.email = email  # goes through the setter, so it is validated

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if "@" not in value:
            raise ValueError("Email must contain '@'.")
        self._email = value

    @abstractmethod
    def borrow_limit(self) -> int:
        """How many items the member may have on loan at once (R3)."""

    @abstractmethod
    def loan_period_days(self) -> int:
        """How many days a loan lasts for this member."""

    @abstractmethod
    def fine_per_day(self) -> int:
        """Fine in rupees for each day an item is late (R5)."""

    @abstractmethod
    def membership_label(self) -> str:
        """Short name of the membership, such as "Student"."""

    def __str__(self) -> str:
        return f"{self.name} ({self.member_id}, {self.membership_label()})"

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(member_id={self.member_id!r}, "
            f"name={self.name!r}, email={self.email!r})"
        )


class StudentMember(Member):
    def borrow_limit(self) -> int:
        return 3

    def loan_period_days(self) -> int:
        return 14

    def fine_per_day(self) -> int:
        return 2

    def membership_label(self) -> str:
        return "Student"


class RegularMember(Member):
    def borrow_limit(self) -> int:
        return 5

    def loan_period_days(self) -> int:
        return 21

    def fine_per_day(self) -> int:
        return 5

    def membership_label(self) -> str:
        return "Regular"


class PremiumMember(Member):
    def borrow_limit(self) -> int:
        return 10

    def loan_period_days(self) -> int:
        return 30

    def fine_per_day(self) -> int:
        return 3

    def membership_label(self) -> str:
        return "Premium"