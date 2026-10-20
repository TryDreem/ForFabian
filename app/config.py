from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://aerdrya:aerdrya@localhost:5432/numbers_db"
    seed_min: int = 0
    seed_max: int = 1_000_000


settings = Settings()
