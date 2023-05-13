from typing import Any

from pydantic import root_validator
from sqlmodel import SQLModel


class ChangesAreNotEmptyMixin(SQLModel):

    @root_validator(pre=True)
    def changes_are_not_empty(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        The validator that checks for the existence of at least one field in the model

        This is necessary for the correct update of the data
        """

        if not values:
            raise ValueError('you must specify at least one field')
        return values
