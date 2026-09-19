from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OllamaHealthRead(BaseModel):
    """Availability of the Ollama service and the configured model."""

    available: bool
    model_available: bool
    ready: bool
    model: str
    error: str | None


class AIAnalysisRead(BaseModel):
    """A persisted AI analysis."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    repository_id: UUID
    model: str
    response: str
    created_at: datetime


class AIAnalysisSummaryRead(BaseModel):
    """A short view of an AI analysis, used on the dashboard."""

    repository_id: UUID
    repository_full_name: str
    model: str
    created_at: datetime
    summary: str
