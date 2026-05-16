from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class DeletionQueryParams(BaseModel):
    mode: Literal["cascade", "reassign"]
    reassign_id: int | None = Field(default=None)

    @model_validator(mode="after")
    def __validator(self) -> Self:
        if self.reassign_id is None and self.mode == "reassign":
            raise ValueError(
                "reassign_id has to be integer when mode is reassign"
            )
        return self
