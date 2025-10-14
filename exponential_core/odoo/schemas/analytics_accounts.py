from pydantic import BaseModel
from typing import List


class AnalyticsSchema(BaseModel):
    id: int
    name: str


AnalyticsSchemaResponse = List[AnalyticsSchema]
