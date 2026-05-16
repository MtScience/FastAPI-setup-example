from typing import Any, AsyncGenerator

from pydantic import BaseModel
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.config import config


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(column_0_name)s",
            "pk": "pk_%(table_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # noqa: E501
        }
    )

    def as_dict(self) -> dict[str, Any]:
        column_data: dict[str, Any] = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)

            if isinstance(value, BaseModel):
                column_data[column.name] = value.model_dump()
            elif isinstance(value, list) and all(
                isinstance(item, BaseModel) for item in value
            ):
                column_data[column.name] = [
                    item.model_dump() for item in value
                ]
            else:
                column_data[column.name] = value
        return column_data


engine = create_async_engine(config.POSTGRES_URL, echo=False)
async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session, session.begin():
        yield session
