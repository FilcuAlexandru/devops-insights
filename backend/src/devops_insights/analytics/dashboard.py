from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from devops_insights.ai.response import extract_section
from devops_insights.analytics.trends import calculate_trend
from devops_insights.models import (
    AIAnalysis,
    CollectionRun,
    Repository,
    RepositorySnapshot,
    Technology,
)
from devops_insights.schemas.ai import AIAnalysisSummaryRead
from devops_insights.schemas.collection import CollectionRunRead
from devops_insights.schemas.dashboard import (
    DashboardRead,
    DashboardTotals,
    GrowthHighlight,
    LanguageShare,
    RepositoryHighlight,
    TechnologyShare,
)
from devops_insights.services.snapshots import load_metric_points

TOP_REPOSITORIES_LIMIT = 10
FASTEST_GROWING_LIMIT = 5
LANGUAGES_LIMIT = 8
RECENT_ANALYSES_LIMIT = 5
UNKNOWN_LANGUAGE = "Unknown"


def build_dashboard(session: Session, technology_slug: str | None = None) -> DashboardRead:
    """Compute every dashboard figure for all technologies or for a single one."""

    def scoped(statement: Select) -> Select:
        return statement.where(Technology.slug == technology_slug) if technology_slug else statement

    repositories = list(
        session.scalars(
            scoped(
                select(Repository)
                .join(Technology)
                .order_by(Repository.stars.desc(), Repository.full_name)
            )
        )
    )

    return DashboardRead(
        totals=_totals(session, repositories),
        technologies=_technology_shares(session, scoped),
        languages=_language_shares(repositories),
        top_repositories=[
            RepositoryHighlight(
                id=repository.id,
                full_name=repository.full_name,
                technology_name=repository.technology.name,
                primary_language=repository.primary_language,
                stars=repository.stars,
                forks=repository.forks,
                open_issues=repository.open_issues,
            )
            for repository in repositories[:TOP_REPOSITORIES_LIMIT]
        ],
        fastest_growing=_fastest_growing(session, repositories),
        recent_analyses=_recent_analyses(session, scoped),
        last_collection=_last_collection(session),
    )


def _totals(session: Session, repositories: list[Repository]) -> DashboardTotals:
    snapshot_count = 0

    if repositories:
        snapshot_count = session.scalar(
            select(func.count(RepositorySnapshot.id)).where(
                RepositorySnapshot.repository_id.in_(repository.id for repository in repositories)
            )
        )

    return DashboardTotals(
        technologies=len({repository.technology_id for repository in repositories}),
        repositories=len(repositories),
        stars=sum(repository.stars for repository in repositories),
        forks=sum(repository.forks for repository in repositories),
        open_issues=sum(repository.open_issues for repository in repositories),
        snapshots=snapshot_count or 0,
    )


def _technology_shares(session: Session, scoped) -> list[TechnologyShare]:
    rows = session.execute(
        scoped(
            select(
                Technology.slug,
                Technology.name,
                func.count(Repository.id),
                func.coalesce(func.sum(Repository.stars), 0),
            )
            .join(Repository, Repository.technology_id == Technology.id)
            .group_by(Technology.id)
            .order_by(func.sum(Repository.stars).desc(), Technology.name)
        )
    )

    return [
        TechnologyShare(slug=slug, name=name, repository_count=count, stars=int(stars))
        for slug, name, count, stars in rows
    ]


def _language_shares(repositories: list[Repository]) -> list[LanguageShare]:
    counts: dict[str, int] = {}

    for repository in repositories:
        language = repository.primary_language or UNKNOWN_LANGUAGE
        counts[language] = counts.get(language, 0) + 1

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))

    return [
        LanguageShare(language=language, repository_count=count)
        for language, count in ranked[:LANGUAGES_LIMIT]
    ]


def _fastest_growing(session: Session, repositories: list[Repository]) -> list[GrowthHighlight]:
    points = load_metric_points(session, (repository.id for repository in repositories))
    highlights: list[GrowthHighlight] = []

    for repository in repositories:
        trend = calculate_trend(points[repository.id])

        if trend.snapshot_count < 2 or trend.change.stars <= 0:
            continue

        highlights.append(
            GrowthHighlight(
                id=repository.id,
                full_name=repository.full_name,
                stars=repository.stars,
                stars_gained=trend.change.stars,
                stars_per_day=trend.stars_per_day,
                snapshot_count=trend.snapshot_count,
            )
        )

    highlights.sort(key=lambda item: (-item.stars_gained, item.full_name))

    return highlights[:FASTEST_GROWING_LIMIT]


def _recent_analyses(session: Session, scoped) -> list[AIAnalysisSummaryRead]:
    rows = session.execute(
        scoped(
            select(AIAnalysis, Repository.full_name)
            .join(Repository, AIAnalysis.repository_id == Repository.id)
            .join(Technology, Repository.technology_id == Technology.id)
            .order_by(AIAnalysis.created_at.desc())
            .limit(RECENT_ANALYSES_LIMIT)
        )
    )

    return [
        AIAnalysisSummaryRead(
            repository_id=analysis.repository_id,
            repository_full_name=full_name,
            model=analysis.model,
            created_at=analysis.created_at,
            summary=extract_section(analysis.response, "Summary"),
        )
        for analysis, full_name in rows
    ]


def _last_collection(session: Session) -> CollectionRunRead | None:
    run = session.scalar(select(CollectionRun).order_by(CollectionRun.started_at.desc()).limit(1))

    return CollectionRunRead.model_validate(run) if run else None
