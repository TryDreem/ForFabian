from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class RandomNumber(Base):
    """Table 1: source numbers."""

    __tablename__ = "random_numbers"

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[int]


class NumberWord(Base):
    """Table 2: the same numbers written out as text (one row per source number)."""

    __tablename__ = "number_words"

    id: Mapped[int] = mapped_column(primary_key=True)
    number_id: Mapped[int] = mapped_column(ForeignKey("random_numbers.id"), unique=True)
    value: Mapped[int]
    text: Mapped[str] = mapped_column(String(255))
