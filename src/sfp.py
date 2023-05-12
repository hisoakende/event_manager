from typing import Any, ItemsView

from fastapi import Query
from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import Field

from src.users.models import User


class SortingFilteringPaging(Filter):
    """The base class that adds pagination to the 'Filter' class of the fastapi_filter package"""

    page: int = Field(Query(ge=0, default=0))
    size: int = Field(Query(ge=1, le=100, default=100))

    def paginate(self, query: Any) -> Any:
        """The function that adds pagination to the database query"""

        return query.offset(self.page * self.size).limit(self.size)

    @property
    def filtering_fields(self) -> ItemsView[str, Any]:
        """The function that separates filterable fields from sorting and pagination fields"""

        fields = self.dict(exclude_none=True, exclude_unset=True)
        fields.pop(self.Constants.ordering_field_name, None)
        fields.pop('page')
        fields.pop('size')
        return fields.items()


class UsersSFP(SortingFilteringPaging):
    """The class that processes sorting, filtering and pagination of users"""

    order_by: list[str] | None = ['-last_name', '-first_name', '-patronymic']

    class Constants(Filter.Constants):
        model = User
