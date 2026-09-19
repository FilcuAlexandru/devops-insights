from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from devops_insights.api.dependencies import DbSession

router = APIRouter(tags=["health"])


@router.get("/health")
def liveness() -> dict[str, str]:
    """Report that the process is running (used for liveness probes)."""

    return {"status": "ok"}


@router.get("/health/ready")
def readiness(session: DbSession) -> dict[str, str]:
    """Report that the application can serve traffic, i.e. the database is reachable."""

    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc

    return {"status": "ready"}
