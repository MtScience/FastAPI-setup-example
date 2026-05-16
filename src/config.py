from dotenv import find_dotenv, load_dotenv
from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings

load_dotenv(find_dotenv(), override=True)


class Config(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def POSTGRES_URL(self) -> str:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            host=self.POSTGRES_HOST,
            path=self.POSTGRES_DB,
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
        ).unicode_string()


config = Config()

__all__ = ["config"]
