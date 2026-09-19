from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from devops_insights.core.config import get_settings
from devops_insights.models import AIAnalysis


def save_ai_analysis(
    session: Session,
    repository_id: UUID,
    context: dict,
    prompt: str,
    response: str,
) -> AIAnalysis:
    """Persist a validated AI analysis."""

    settings = get_settings()

    analysis = AIAnalysis(
        repository_id=repository_id,
        model=settings.ollama_model,
        prompt=prompt,
        context=context,
        response=response,
    )

    session.add(analysis)
    session.commit()
    session.refresh(analysis)

    return analysis


def get_repository_analyses(
    session: Session,
    repository_id: UUID,
) -> list[AIAnalysis]:
    """Return persisted analyses for a repository."""

    return list(
        session.scalars(
            select(AIAnalysis)
            .where(AIAnalysis.repository_id == repository_id)
            .order_by(AIAnalysis.created_at.desc())
        ).all()
    )
