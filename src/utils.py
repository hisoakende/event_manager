from typing import Any

from pydantic import root_validator
from sqlmodel import SQLModel


class ChangesAreNotEmptyMixin(SQLModel):

    @root_validator
    def changes_are_empty(cls, values: dict[str, Any]) -> dict[str, Any]:
        if all(value is None for value in values.values()):
            raise ValueError('you must specify at least one field')

        return values
