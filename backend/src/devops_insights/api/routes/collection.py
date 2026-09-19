from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from sqlalchemy import select

from devops_insights.api.dependencies import DbSession
from devops_insights.collectors.github import GitHubClient
from devops_insights.models import CollectionRun, CollectionTrigger
from devops_insights.schemas.collection import CollectionRunRead
from devops_insights.services.collection import create_run, execute_run, get_active_run

router = APIRouter(prefix="/api/collection", tags=["collection"])


def _execute_in_background(run_id: UUID) -> None:
    client = GitHubClient.from_settings()

    try:
        execute_run(run_id, client)
    finally:
        client.close()


@router.get("/runs", response_model=list[CollectionRunRead])
def list_runs(session: DbSession, limit: int = Query(10, ge=1, le=100)) -> list[CollectionRun]:
    """Return the most recent collection runs, newest first."""

    return list(
        session.scalars(
            select(CollectionRun).order_by(CollectionRun.started_at.desc()).limit(limit)
        )
    )


@router.post("/run", response_model=CollectionRunRead, status_code=status.HTTP_202_ACCEPTED)
def start_run(session: DbSession, background_tasks: BackgroundTasks) -> CollectionRun:
    """Start a collection run in the background and return it immediately."""

    if get_active_run(session) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A collection run is already in progress.",
        )

    run = create_run(session, CollectionTrigger.MANUAL)
    background_tasks.add_task(_execute_in_background, run.id)

    return run
