from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from devops_insights.ai.analysis import analyze_repository
from devops_insights.ai.errors import AIServiceError, InvalidAIResponseError
from devops_insights.ai.health import check_ollama_health
from devops_insights.ai.persistence import get_repository_analyses
from devops_insights.api.dependencies import DbSession
from devops_insights.schemas.ai import AIAnalysisRead, OllamaHealthRead
from devops_insights.services.repositories import get_repository

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/health", response_model=OllamaHealthRead)
def ai_health() -> OllamaHealthRead:
    """Return the health status of the AI service."""

    health = check_ollama_health()

    return OllamaHealthRead(
        available=health.available,
        model_available=health.model_available,
        ready=health.ready,
        model=health.model,
        error=health.error,
    )


@router.post("/repositories/{repository_id}/analyze", response_model=AIAnalysisRead)
def analyze_repository_endpoint(repository_id: UUID, session: DbSession) -> AIAnalysisRead:
    """Generate and persist an AI analysis for a repository."""

    if get_repository(session, repository_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")

    health = check_ollama_health()

    if not health.ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health.error or "The AI service is not ready.",
        )

    try:
        analysis = analyze_repository(session, repository_id)
    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except InvalidAIResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"The model returned an invalid analysis: {exc}",
        ) from exc

    return AIAnalysisRead.model_validate(analysis)


@router.get("/repositories/{repository_id}/analyses", response_model=list[AIAnalysisRead])
def list_analyses(repository_id: UUID, session: DbSession) -> list[AIAnalysisRead]:
    """Return the persisted AI analyses of a repository, newest first."""

    if get_repository(session, repository_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")

    return [
        AIAnalysisRead.model_validate(analysis)
        for analysis in get_repository_analyses(session, repository_id)
    ]
