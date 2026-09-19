from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from devops_insights.catalog import CATALOG, TechnologyDefinition
from devops_insights.models import Technology


def sync_catalog(
    session: Session,
    catalog: Iterable[TechnologyDefinition] = CATALOG,
) -> dict[str, Technology]:
    """Create or update a technology row for every catalog entry.

    Returns the technologies keyed by slug. The function is idempotent, so it is safe
    to run before every collection.
    """

    catalog = tuple(catalog)
    existing = {
        technology.slug: technology
        for technology in session.scalars(
            select(Technology).where(Technology.slug.in_(entry.slug for entry in catalog))
        )
    }

    for entry in catalog:
        technology = existing.get(entry.slug)

        if technology is None:
            technology = Technology(slug=entry.slug)
            session.add(technology)
            existing[entry.slug] = technology

        technology.name = entry.name
        technology.category = entry.category
        technology.description = entry.description
        technology.website_url = entry.website_url

    session.commit()

    return existing
