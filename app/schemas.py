from pydantic import BaseModel, ConfigDict


class RandomNumberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    value: int


class NumberWordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number_id: int
    value: int
    text: str


class ConvertResult(BaseModel):
    converted: int
