import logging

from sqlalchemy.orm import Session

from devops_insights.collectors.github import GitHubClient
from devops_insights.models import Repository, Technology
from devops_insights.observability.metrics import (
    record_collection_error,
    record_repository_collected,
)
from devops_insights.pipelines.normalize import normalize_repository
from devops_insights.pipelines.store import store_repository

logger = logging.getLogger(__name__)


def collect_repository(
    session: Session,
    client: GitHubClient,
    technology: Technology,
    full_name: str,
) -> Repository:
    """Fetch, normalize and persist one GitHub repository."""

    try:
        extracted = client.fetch_repository(full_name)
        normalized = normalize_repository(extracted)
        repository = store_repository(session, normalized, technology)
    except Exception:
        session.rollback()
        record_collection_error()
        logger.exception("GitHub pipeline failed for %s", full_name)
        raise

    record_repository_collected()

    return repository
