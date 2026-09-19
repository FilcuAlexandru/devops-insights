from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from devops_insights.analytics.dashboard import build_dashboard
from devops_insights.api.dependencies import DbSession
from devops_insights.models import Technology
from devops_insights.schemas.dashboard import DashboardRead

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardRead)
def get_dashboard(
    session: DbSession,
    technology: str | None = Query(None, description="Limit the dashboard to one technology slug."),
) -> DashboardRead:
    """Return the dashboard figures for all technologies or for one of them."""

    if (
        technology
        and session.scalar(select(Technology.id).where(Technology.slug == technology)) is None
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technology not found.")

    return build_dashboard(session, technology)
