import datetime

from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import Field

from src.events.models import Event
from src.sfp import SortingFilteringPaging


class EventsSFP(SortingFilteringPaging):
    """The class that processes sorting, filtering and pagination of events"""

    order_by: list[str] | None = ['name', 'is_active']

    datetime__gte: datetime.datetime | None = Field(alias='starting_from')
    datetime__lte: datetime.datetime | None = Field(alias='ending_in')

    class Constants(Filter.Constants):
        model = Event
