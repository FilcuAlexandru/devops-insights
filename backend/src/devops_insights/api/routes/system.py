from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from devops_insights import __version__
from devops_insights.ai.health import check_ollama_health
from devops_insights.api.dependencies import DbSession
from devops_insights.core.config import get_settings
from devops_insights.models import CollectionRun
from devops_insights.schemas.ai import OllamaHealthRead
from devops_insights.schemas.collection import CollectionRunRead

router = APIRouter(prefix="/api", tags=["status"])


class ServiceStatus(BaseModel):
    """Overall platform status."""

    version: str
    environment: str
    database_ok: bool
    ollama: OllamaHealthRead
    last_collection: CollectionRunRead | None


@router.get("/status", response_model=ServiceStatus)
def platform_status(session: DbSession) -> ServiceStatus:
    """Report the health of the platform's dependencies."""

    settings = get_settings()

    try:
        session.execute(text("SELECT 1"))
        database_ok = True
        run = session.scalar(
            select(CollectionRun).order_by(CollectionRun.started_at.desc()).limit(1)
        )
    except SQLAlchemyError:
        database_ok = False
        run = None

    health = check_ollama_health()

    return ServiceStatus(
        version=__version__,
        environment=settings.app_env,
        database_ok=database_ok,
        ollama=OllamaHealthRead(
            available=health.available,
            model_available=health.model_available,
            ready=health.ready,
            model=health.model,
            error=health.error,
        ),
        last_collection=CollectionRunRead.model_validate(run) if run else None,
    )
