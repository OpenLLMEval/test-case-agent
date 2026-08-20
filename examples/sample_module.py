"""Sample module used to demonstrate testcase-agent generation."""

from __future__ import annotations


def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b


def divide(numerator: float, denominator: float) -> float:
    """Divide numerator by denominator."""
    if denominator == 0:
        raise ValueError("denominator must not be zero")
    return numerator / denominator


class UserService:
    """Manage basic user lifecycle operations."""

    def create_user(self, email: str, age: int) -> dict:
        """Create a user record from email and age."""
        if not email or "@" not in email:
            raise ValueError("invalid email")
        if age < 0:
            raise ValueError("age must be non-negative")
        return {"email": email, "age": age}
