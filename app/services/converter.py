from num2words import num2words
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import NumberWord, RandomNumber


def number_to_text(number: int) -> str:
    """7 -> 'seven', 42 -> 'forty-two'."""
    return num2words(number, lang="en")


def convert_pending(session: Session) -> int:
    """Convert every number of table 1 that is not in table 2 yet.

    Safe to call repeatedly: already converted numbers are skipped.
    Returns how many numbers were converted.
    """
    already_converted = select(NumberWord.number_id)
    pending = session.scalars(
        select(RandomNumber)
        .where(RandomNumber.id.not_in(already_converted))
        .order_by(RandomNumber.id)
    ).all()

    session.add_all(
        NumberWord(number_id=n.id, value=n.value, text=number_to_text(n.value)) for n in pending
    )
    session.commit()
    return len(pending)
