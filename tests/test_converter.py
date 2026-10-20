import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import NumberWord, RandomNumber
from app.services.converter import convert_pending, number_to_text


@pytest.mark.parametrize(
    ("number", "text"),
    [(0, "zero"), (7, "seven"), (42, "forty-two"), (1000, "one thousand")],
)
def test_number_to_text(number: int, text: str) -> None:
    assert number_to_text(number) == text


def test_convert_pending_only_converts_new_numbers(session: Session) -> None:
    session.add_all([RandomNumber(value=7), RandomNumber(value=42)])
    session.commit()

    assert convert_pending(session) == 2
    assert convert_pending(session) == 0

    session.add(RandomNumber(value=3))
    session.commit()
    assert convert_pending(session) == 1

    texts = session.scalars(select(NumberWord.text).order_by(NumberWord.id)).all()
    assert texts == ["seven", "forty-two", "three"]
