import logging
import time
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from devops_insights.catalog import CATALOG, TechnologyDefinition
from devops_insights.collectors.github import GitHubClient, GitHubRateLimitError
from devops_insights.core.database import SessionLocal
from devops_insights.models import CollectionRun, CollectionStatus, CollectionTrigger
from devops_insights.models.base import utc_now
from devops_insights.observability.metrics import record_collection_run
from devops_insights.pipelines.github import collect_repository
from devops_insights.services.catalog import sync_catalog

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], Session]

# A run that has been "running" for longer than this is assumed to have crashed.
STALE_RUN_AFTER = timedelta(minutes=30)


@dataclass(frozen=True)
class CollectionSummary:
    """The outcome of a finished collection run."""

    run_id: uuid.UUID
    status: CollectionStatus
    total: int
    succeeded: int
    failed: int


def count_targets(catalog: Iterable[TechnologyDefinition] = CATALOG) -> int:
    """Return the number of repositories a collection run will visit."""

    return sum(len(entry.repositories) for entry in catalog)


def get_active_run(session: Session) -> CollectionRun | None:
    """Return the collection run currently in progress, if any.

    Runs that have been in progress for too long are marked as failed and ignored.
    """

    running = session.scalars(
        select(CollectionRun).where(CollectionRun.status == CollectionStatus.RUNNING)
    ).all()

    active: CollectionRun | None = None

    for run in running:
        if utc_now() - run.started_at > STALE_RUN_AFTER:
            run.status = CollectionStatus.FAILED
            run.finished_at = utc_now()
            run.errors = [*run.errors, {"repository": "*", "error": "Run was interrupted."}]
        else:
            active = run

    session.commit()

    return active


def create_run(
    session: Session,
    trigger: CollectionTrigger,
    catalog: tuple[TechnologyDefinition, ...] = CATALOG,
) -> CollectionRun:
    """Record the start of a collection run."""

    run = CollectionRun(
        trigger=trigger,
        status=CollectionStatus.RUNNING,
        total=count_targets(catalog),
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    return run


def execute_run(
    run_id: uuid.UUID,
    client: GitHubClient,
    session_factory: SessionFactory = SessionLocal,
    catalog: tuple[TechnologyDefinition, ...] = CATALOG,
) -> CollectionSummary:
    """Collect every catalog repository and finalize the given run.

    A failure of a single repository is recorded and does not stop the run. An unexpected
    error (for example the database going away) marks the whole run as failed and is re-raised.
    """

    try:
        return _collect_catalog(run_id, client, session_factory, catalog)
    except Exception as exc:
        _mark_run_failed(run_id, session_factory, str(exc))
        raise


def _mark_run_failed(run_id: uuid.UUID, session_factory: SessionFactory, reason: str) -> None:
    try:
        with session_factory() as session:
            session.rollback()
            run = session.get(CollectionRun, run_id)

            if run is not None and run.status == CollectionStatus.RUNNING:
                run.status = CollectionStatus.FAILED
                run.finished_at = utc_now()
                run.errors = [*run.errors, {"repository": "*", "error": reason}]
                session.commit()
    except Exception:
        logger.exception("Could not mark collection run %s as failed.", run_id)


def _collect_catalog(
    run_id: uuid.UUID,
    client: GitHubClient,
    session_factory: SessionFactory,
    catalog: tuple[TechnologyDefinition, ...],
) -> CollectionSummary:
    started = time.perf_counter()
    errors: list[dict[str, str]] = []
    succeeded = 0

    with session_factory() as session:
        technologies = sync_catalog(session, catalog)
        targets = [(entry.slug, name) for entry in catalog for name in entry.repositories]

        for index, (slug, full_name) in enumerate(targets):
            try:
                collect_repository(session, client, technologies[slug], full_name)
            except GitHubRateLimitError as exc:
                errors.extend(
                    {"repository": remaining, "error": str(exc)} for _, remaining in targets[index:]
                )
                break
            except Exception as exc:
                errors.append({"repository": full_name, "error": str(exc)})
            else:
                succeeded += 1

        run = session.get(CollectionRun, run_id)
        run.total = len(targets)
        run.succeeded = succeeded
        run.failed = len(errors)
        run.errors = errors
        run.status = _resolve_status(succeeded, len(errors))
        run.finished_at = utc_now()
        session.commit()

        summary = CollectionSummary(
            run_id=run.id,
            status=CollectionStatus(run.status),
            total=run.total,
            succeeded=run.succeeded,
            failed=run.failed,
        )

    record_collection_run(summary.status, time.perf_counter() - started)
    logger.info(
        "Collection %s finished: status=%s succeeded=%d failed=%d",
        summary.run_id,
        summary.status,
        summary.succeeded,
        summary.failed,
    )

    return summary


def run_collection(
    trigger: CollectionTrigger,
    client: GitHubClient,
    session_factory: SessionFactory = SessionLocal,
    catalog: tuple[TechnologyDefinition, ...] = CATALOG,
) -> CollectionSummary:
    """Create a collection run and execute it immediately."""

    with session_factory() as session:
        run_id = create_run(session, trigger, catalog).id

    return execute_run(run_id, client, session_factory, catalog)


def _resolve_status(succeeded: int, failed: int) -> CollectionStatus:
    if failed == 0:
        return CollectionStatus.SUCCEEDED

    return CollectionStatus.PARTIAL if succeeded else CollectionStatus.FAILED
