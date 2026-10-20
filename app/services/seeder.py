import random

from sqlalchemy.orm import Session

from app.models import RandomNumber


def seed_numbers(session: Session, count: int, low: int, high: int) -> list[RandomNumber]:
    """Insert `count` random numbers between `low` and `high` into table 1."""
    numbers = [RandomNumber(value=random.randint(low, high)) for _ in range(count)]
    session.add_all(numbers)
    session.commit()
    return numbers
