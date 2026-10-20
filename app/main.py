from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query
from sqlalchemy import select

from app.config import settings
from app.db import Base, SessionDep, engine
from app.models import NumberWord, RandomNumber
from app.schemas import ConvertResult, NumberWordOut, RandomNumberOut
from app.services.converter import convert_pending
from app.services.seeder import seed_numbers


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Number to text service", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/seed")
def seed(
    session: SessionDep, count: Annotated[int, Query(ge=1, le=10_000)] = 20
) -> list[RandomNumberOut]:
    """Fill table 1 with random numbers."""
    return seed_numbers(session, count, settings.seed_min, settings.seed_max)


@app.post("/convert")
def convert(session: SessionDep) -> ConvertResult:
    """Convert new numbers of table 1 to text and store them in table 2."""
    return ConvertResult(converted=convert_pending(session))


@app.get("/numbers")
def list_numbers(session: SessionDep) -> list[RandomNumberOut]:
    """Content of table 1."""
    return session.scalars(select(RandomNumber).order_by(RandomNumber.id)).all()


@app.get("/words")
def list_words(session: SessionDep) -> list[NumberWordOut]:
    """Content of table 2."""
    return session.scalars(select(NumberWord).order_by(NumberWord.id)).all()
