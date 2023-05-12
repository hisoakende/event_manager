from fastapi_filter.contrib.sqlalchemy import Filter

from src.gov_structures.models import GovStructure
from src.sfp import SortingFilteringPaging


class GovStructureSFP(SortingFilteringPaging):
    """The class that processes sorting, filtering and pagination of government structures"""

    order_by: list[str] | None = ['name']

    class Constants(Filter.Constants):
        model = GovStructure
