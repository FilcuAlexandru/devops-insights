from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CollectionErrorRead(BaseModel):
    """A repository that could not be collected."""

    repository: str
    error: str


class CollectionRunRead(BaseModel):
    """One execution of the collection pipeline."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trigger: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    total: int
    succeeded: int
    failed: int
    errors: list[CollectionErrorRead]
